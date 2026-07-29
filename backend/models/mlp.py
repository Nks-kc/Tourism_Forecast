import logging
import pickle

import numpy as np
from config import MLP_BATCH_SIZE, MLP_EPOCHS, MLP_HIDDEN_SIZES, MLP_LEARNING_RATE

from models.scaler import StandardScaler

logger = logging.getLogger(__name__)


class MLP:
    def __init__(
        self,
        input_size: int,
        hidden_sizes: list | None = None,
        learning_rate: float = MLP_LEARNING_RATE,
        epochs: int = MLP_EPOCHS,
        batch_size: int = MLP_BATCH_SIZE,
        random_state: int = 42,
    ):
        self.random_state = random_state
        if self.random_state is not None:
            np.random.seed(self.random_state)
        if hidden_sizes is None:
            hidden_sizes = MLP_HIDDEN_SIZES
        self.hidden_sizes = hidden_sizes
        self.lr = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.layer_sizes = [input_size] + hidden_sizes + [1]
        self.weights = []
        self.biases = []
        self.scaler = StandardScaler()
        self.loss_history: list[float] = []
        self.best_loss = np.inf
        self.is_fitted = False
        for i in range(len(self.layer_sizes) - 1):
            n_in = self.layer_sizes[i]
            n_out = self.layer_sizes[i + 1]
            weight = np.random.randn(n_in, n_out) * np.sqrt(2.0 / n_in)
            bias = np.zeros((1, n_out))
            self.weights.append(weight)
            self.biases.append(bias)

    def _relu(self, z: np.ndarray) -> np.ndarray:
        return np.maximum(0, z)

    def _relu_grad(self, z: np.ndarray) -> np.ndarray:
        return (z > 0).astype(float)

    def forward(self, X: np.ndarray) -> np.ndarray:
        self.activations = [X]
        self.z_values = []
        current = X
        for i, (W, b) in enumerate(zip(self.weights, self.biases)):
            z = current @ W + b
            self.z_values.append(z)
            is_last_layer = i == len(self.weights) - 1
            if is_last_layer:
                current = z
            else:
                current = self._relu(z)
            self.activations.append(current)
        return current

    def compute_loss(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        return float(np.mean((y_pred - y_true) ** 2))

    def backward(self, y_true: np.ndarray):
        n = y_true.shape[0]
        self.grad_weights = [None] * len(self.weights)
        self.grad_biases = [None] * len(self.biases)
        delta = 2.0 * (self.activations[-1] - y_true) / n
        for i in reversed(range(len(self.weights))):
            self.grad_weights[i] = self.activations[i].T @ delta
            self.grad_biases[i] = np.sum(delta, axis=0, keepdims=True)
            if i > 0:
                delta = delta @ self.weights[i].T
                delta = delta * self._relu_grad(self.z_values[i - 1])

    def _update_weights(self):
        for i in range(len(self.weights)):
            self.weights[i] -= self.lr * self.grad_weights[i]
            self.biases[i] -= self.lr * self.grad_biases[i]

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int | None = None,
        batch_size: int | None = None,
        val_data=None,
        verbose: bool = True,
    ) -> dict:
        if epochs is None:
            epochs = self.epochs
        if batch_size is None:
            batch_size = self.batch_size
        X = self.scaler.fit_transform(X)
        if val_data is not None:
            X_val, y_val = val_data
            X_val = self.scaler.transform(X_val)
            val_data = (X_val, y_val)
        n = X.shape[0]
        history = {"train_loss": [], "val_loss": []}
        self.loss_history.clear()
        for epoch in range(epochs):
            permutation = np.random.permutation(n)
            X_shuffled = X[permutation]
            y_shuffled = y[permutation]
            batch_losses = []
            for start in range(0, n, batch_size):
                end = start + batch_size
                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]
                y_pred = self.forward(X_batch)
                loss = self.compute_loss(y_pred, y_batch)
                batch_losses.append(loss)
                self.backward(y_batch)
                self._update_weights()
            avg_loss = float(np.mean(batch_losses))
            history["train_loss"].append(avg_loss)
            self.loss_history.append(avg_loss)
            if val_data is not None:
                X_val, y_val = val_data
                val_pred = self.forward(X_val)
                val_loss = self.compute_loss(val_pred, y_val)
                history["val_loss"].append(float(val_loss))
                self.best_loss = min(self.best_loss, val_loss)
            if verbose and ((epoch + 1) % 100 == 0 or epoch == 0):
                if val_data is not None:
                    logger.info(
                        "Epoch %4d/%d | Train Loss: %.6f | Val Loss: %.6f",
                        epoch + 1,
                        epochs,
                        avg_loss,
                        val_loss,
                    )
                else:
                    logger.info(
                        "Epoch %4d/%d | Train Loss: %.6f", epoch + 1, epochs, avg_loss
                    )
        self.is_fitted = True
        return history

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs):
        return self.train(X, y, **kwargs)

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError(
                "The model has not been trained yet. Call train() first."
            )
        X_scaled = self.scaler.transform(X)
        predictions = self.forward(X_scaled)
        return predictions

    def save_model(self, filepath: str) -> None:
        if not self.is_fitted:
            raise RuntimeError("Cannot save an untrained model.")
        model_data = {
            "layer_sizes": self.layer_sizes,
            "hidden_sizes": self.hidden_sizes,
            "learning_rate": self.lr,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "random_state": self.random_state,
            "weights": self.weights,
            "biases": self.biases,
            "loss_history": self.loss_history,
            "best_loss": self.best_loss,
            "scaler_mean": self.scaler.mean_,
            "scaler_std": self.scaler.std_,
        }
        with open(filepath, "wb") as file:
            pickle.dump(model_data, file)
        logger.info("MLP model saved to %s", filepath)

    @classmethod
    def load_model(cls, filepath: str):
        with open(filepath, "rb") as file:
            model_data = pickle.load(file)
        input_size = model_data["layer_sizes"][0]
        model = cls(
            input_size=input_size,
            hidden_sizes=model_data["hidden_sizes"],
            learning_rate=model_data["learning_rate"],
            epochs=model_data["epochs"],
            batch_size=model_data["batch_size"],
            random_state=model_data.get("random_state", 42),
        )
        model.weights = model_data["weights"]
        model.biases = model_data["biases"]
        model.loss_history = model_data.get("loss_history", [])
        model.best_loss = model_data.get("best_loss", np.inf)
        model.scaler.set_params(model_data["scaler_mean"], model_data["scaler_std"])
        model.is_fitted = True
        logger.info("MLP model loaded from %s", filepath)
        return model

    def save(self, filepath: str):
        self.save_model(filepath)

    @classmethod
    def load(cls, filepath: str):
        return cls.load_model(filepath)
