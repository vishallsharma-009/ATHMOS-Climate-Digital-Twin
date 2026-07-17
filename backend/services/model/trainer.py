import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import logging

logger = logging.getLogger("athmos.model.trainer")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class ClimateModelTrainer:
    """
    Handles the training and validation loops for the ConvLSTM model.
    """
    def __init__(self, model, learning_rate=1e-3, device=None, checkpoint_dir="checkpoints"):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        # MSE is standard for continuous meteorological variables
        self.criterion = nn.MSELoss() 
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        logger.info(f"Initialized trainer on device: {self.device}")

    def train_epoch(self, dataloader):
        self.model.train()
        total_loss = 0.0
        
        for batch_idx, (x, y) in enumerate(dataloader):
            x = x.to(self.device)
            y = y.to(self.device)
            
            self.optimizer.zero_grad()
            
            # Predict autoregressively for the full horizon (y.size(1))
            horizon = y.size(1)
            preds = self.model.predict(x, horizon=horizon) # [B, horizon, C, H, W]
            
            # Compute MSE loss over the entire predicted sequence
            mse_loss = self.criterion(preds, y)
            
            # ----------------------------------------------------
            # PHYSICS-INFORMED LOSS PENALTIES
            # ----------------------------------------------------
            # Assuming channel indices based on app.py:
            # 0: imd_rainfall, 1: tmax, 2: tmin, 5: insat_rainfall
            
            # 1. Temperature Inversion Penalty (TMin should never exceed TMax)
            # Penalize the model if TMin > TMax
            tmax = preds[:, :, 1, :, :]
            tmin = preds[:, :, 2, :, :]
            temp_penalty = torch.relu(tmin - tmax).mean()
            
            # 2. Non-Negative Rainfall Penalty
            rain_imd = preds[:, :, 0, :, :]
            rain_insat = preds[:, :, 5, :, :]
            rain_penalty = torch.relu(-rain_imd).mean() + torch.relu(-rain_insat).mean()
            
            # Combine standard MSE with physical constraints
            loss = mse_loss + 0.1 * temp_penalty + 0.1 * rain_penalty

            loss.backward()
            
            # Gradient clipping to prevent exploding gradients in LSTMs
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            
            total_loss += loss.item()
            
        return total_loss / len(dataloader)

    def validate(self, dataloader):
        self.model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for x, y in dataloader:
                x = x.to(self.device)
                y = y.to(self.device)
                
                horizon = y.size(1)
                preds = self.model.predict(x, horizon=horizon)
                
                loss = self.criterion(preds, y)
                total_loss += loss.item()
                
        return total_loss / len(dataloader)

    def fit(self, train_dataset, val_dataset, epochs=10, batch_size=4):
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        best_val_loss = float('inf')
        
        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader)
            
            logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.save_checkpoint("best_model.pt", epoch=epoch, val_loss=val_loss)
                logger.info(f"Saved new best model with Val Loss: {best_val_loss:.4f}")

    def save_checkpoint(self, filename, epoch=None, val_loss=None):
        path = os.path.join(self.checkpoint_dir, filename)
        torch.save({
            'epoch': epoch,
            'val_loss': val_loss,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, path)

    def load_checkpoint(self, filename):
        path = os.path.join(self.checkpoint_dir, filename)
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        epoch = checkpoint.get('epoch', 'Unknown')
        val_loss = checkpoint.get('val_loss', 'Unknown')
        logger.info(f"Loaded checkpoint from {path} (Epoch: {epoch}, Val Loss: {val_loss})")
