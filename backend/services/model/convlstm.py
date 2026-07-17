import torch
import torch.nn as nn

class ConvLSTMCell(nn.Module):
    """
    A single ConvLSTM Cell.
    """
    def __init__(self, input_dim, hidden_dim, kernel_size, bias=True):
        super(ConvLSTMCell, self).__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.padding = kernel_size[0] // 2, kernel_size[1] // 2
        self.bias = bias

        self.conv = nn.Conv2d(
            in_channels=self.input_dim + self.hidden_dim,
            out_channels=4 * self.hidden_dim,
            kernel_size=self.kernel_size,
            padding=self.padding,
            bias=self.bias
        )

    def forward(self, input_tensor, cur_state):
        h_cur, c_cur = cur_state

        combined = torch.cat([input_tensor, h_cur], dim=1)  # concatenate along channel axis
        combined_conv = self.conv(combined)

        cc_i, cc_f, cc_o, cc_g = torch.split(combined_conv, self.hidden_dim, dim=1)
        i = torch.sigmoid(cc_i)
        f = torch.sigmoid(cc_f)
        o = torch.sigmoid(cc_o)
        g = torch.tanh(cc_g)

        c_next = f * c_cur + i * g
        h_next = o * torch.tanh(c_next)

        return h_next, c_next

    def init_hidden(self, batch_size, image_size):
        height, width = image_size
        return (
            torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device),
            torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device)
        )


class ConvLSTM(nn.Module):
    """
    ConvLSTM architecture capable of handling multiple variables (channels).
    """
    def __init__(self, input_dim, hidden_dims, kernel_size=(3, 3), bias=True, num_layers=2):
        super(ConvLSTM, self).__init__()

        self.input_dim = input_dim
        
        # If a single int is passed for hidden dims, expand to list
        if isinstance(hidden_dims, int):
            self.hidden_dims = [hidden_dims] * num_layers
        else:
            self.hidden_dims = hidden_dims
            
        self.num_layers = len(self.hidden_dims)

        cell_list = []
        for i in range(self.num_layers):
            cur_input_dim = self.input_dim if i == 0 else self.hidden_dims[i - 1]
            cell_list.append(ConvLSTMCell(
                input_dim=cur_input_dim,
                hidden_dim=self.hidden_dims[i],
                kernel_size=kernel_size,
                bias=bias
            ))

        self.cell_list = nn.ModuleList(cell_list)
        
        # Output layer maps the final hidden state back to the input channels
        self.final_conv = nn.Conv2d(
            in_channels=self.hidden_dims[-1],
            out_channels=self.input_dim,
            kernel_size=(1, 1),
            bias=True
        )

    def forward(self, input_tensor, hidden_state=None):
        """
        input_tensor: [batch_size, seq_len, channels, height, width]
        """
        b, seq_len, _, h, w = input_tensor.size()

        if hidden_state is None:
            hidden_state = self._init_hidden(b, (h, w), input_tensor.device)

        current_input = input_tensor

        for layer_idx in range(self.num_layers):
            h_inner, c_inner = hidden_state[layer_idx]
            
            output_inner = []
            for t in range(seq_len):
                h_inner, c_inner = self.cell_list[layer_idx](
                    current_input[:, t, :, :, :], (h_inner, c_inner)
                )
                output_inner.append(h_inner)

            # Reconstruct sequence dimension for next layer
            current_input = torch.stack(output_inner, dim=1)
            hidden_state[layer_idx] = (h_inner, c_inner)

        # Map back to original channels
        b, s, c, h, w = current_input.size()
        out = current_input.view(b * s, c, h, w)
        out = self.final_conv(out)
        out = out.view(b, s, self.input_dim, h, w)
        
        return out, hidden_state

    def _init_hidden(self, batch_size, image_size, device):
        init_states = []
        for i in range(self.num_layers):
            init_states.append(
                (torch.zeros(batch_size, self.hidden_dims[i], *image_size, device=device),
                 torch.zeros(batch_size, self.hidden_dims[i], *image_size, device=device))
            )
        return init_states

    def predict(self, input_tensor, horizon=1):
        """
        Autoregressive prediction for `horizon` steps into the future.
        """
        outputs = []
        # Get hidden state from history
        out, hidden = self.forward(input_tensor)
        
        # The predicted next step is the last output of the sequence
        last_pred = out[:, -1:, :, :, :] # Shape: [B, 1, C, H, W]
        outputs.append(last_pred)
        
        # Autoregressively feed prediction back in
        for _ in range(1, horizon):
            out, hidden = self.forward(last_pred, hidden)
            last_pred = out[:, -1:, :, :, :]
            outputs.append(last_pred)
            
        return torch.cat(outputs, dim=1) # [B, horizon, C, H, W]
