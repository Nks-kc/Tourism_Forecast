"""
models/mlp.py
-------------
Multi-Layer Perceptron (MLP) implemented from scratch using NumPy only.
No PyTorch. No TensorFlow. No sklearn MLPRegressor.

HOW A NEURAL NETWORK LEARNS (plain English):
  Imagine you have a dial (a weight) that controls how much each input
  affects the output. At the start the dials are set randomly.

  Training loop:
    1. FORWARD PASS  — Feed data in, get a prediction out
    2. LOSS          — Measure how wrong the prediction is (MSE)
    3. BACKWARD PASS — Figure out which dials caused the error (gradients)
    4. UPDATE        — Slightly turn every dial to reduce the error
    5. REPEAT        — Do this thousands of times until predictions are good

ARCHITECTURE for this project:
  Input (10 features) → Hidden Layer 64 → Hidden Layer 32 → Output (1 number)

ACTIVATION FUNCTIONS:
  Hidden layers use ReLU: f(x) = max(0, x)
    → Negative values become 0, positive values pass through unchanged.
    → This introduces non-linearity so the network can learn complex patterns.
  Output layer uses Linear (no activation)
    → We want a raw number, not a probability, so no squishing needed.
"""

import numpy as np

import logging
import pickle

from config import (
    MLP_HIDDEN_SIZES,
    MLP_LEARNING_RATE,
    MLP_EPOCHS,
    MLP_BATCH_SIZE,
)

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
        """
        Build the neural network and initialize all parameters.

        Args:
            input_size:
                Number of input features.

            hidden_sizes:
                List containing the number of neurons in each hidden layer.
                Example: [64, 32]

            learning_rate:
                Gradient descent learning rate.

            epochs:
                Number of training epochs.

            batch_size:
                Mini-batch size.

            random_state:
                Random seed used for reproducible weight initialization.
        """

        # -------------------------
        # Reproducibility
        # -------------------------
        self.random_state = random_state

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # -------------------------
        # Hyperparameters
        # -------------------------
        if hidden_sizes is None:
            hidden_sizes = MLP_HIDDEN_SIZES

        self.hidden_sizes = hidden_sizes
        self.lr = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size

        # -------------------------
        # Network Architecture
        # -------------------------
        self.layer_sizes = [input_size] + hidden_sizes + [1]

        # -------------------------
        # Model Parameters
        # -------------------------
        self.weights = []
        self.biases = []

        # -------------------------
        # Training Utilities
        # -------------------------
        self.scaler = StandardScaler()

        self.loss_history: list[float] = []

        self.best_loss = np.inf

        self.is_fitted = False

        # -------------------------
        # Weight Initialization
        # -------------------------
        for i in range(len(self.layer_sizes) - 1):

            n_in = self.layer_sizes[i]
            n_out = self.layer_sizes[i + 1]

            # He Initialization
            weight = np.random.randn(n_in, n_out) * np.sqrt(2.0 / n_in)

            bias = np.zeros((1, n_out))

            self.weights.append(weight)
            self.biases.append(bias)

    # ──────────────────────────────────────────────────────────────────────────
    # Activation functions
    # ──────────────────────────────────────────────────────────────────────────

    def _relu(self, z: np.ndarray) -> np.ndarray:
        """ReLU activation: max(0, z). Negative → 0, positive → unchanged."""
        return np.maximum(0, z)

    def _relu_grad(self, z: np.ndarray) -> np.ndarray:
        """
        Derivative of ReLU.
        f'(z) = 1 if z > 0, else 0.
        Used in backpropagation to "pass" gradients through ReLU.
        """
        return (z > 0).astype(float)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 1 — Forward pass
    # ──────────────────────────────────────────────────────────────────────────

    def forward(self, X: np.ndarray) -> np.ndarray:
        """
        Pass input data through every layer to get a prediction.

        For each layer i:
            z_i = a_{i-1} @ W_i + b_i    ← linear combination
            a_i = ReLU(z_i)               ← activation (except last layer)

        We save z_values and activations because backprop needs them.

        Args:
            X: Input array, shape (batch_size, n_features)

        Returns:
            Predictions, shape (batch_size, 1)
        """
        # Store inputs and all intermediate activations
        self.activations = [X]
        self.z_values    = []

        current = X
        for i, (W, b) in enumerate(zip(self.weights, self.biases)):

            # Linear step: z = input @ weights + bias
            z = current @ W + b
            self.z_values.append(z)

            is_last_layer = (i == len(self.weights) - 1)
            if is_last_layer:
                # Output layer: linear (no activation) — we want raw numbers
                current = z
            else:
                # Hidden layer: apply ReLU
                current = self._relu(z)

            self.activations.append(current)

        return current  # final predictions

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 2 — Loss function
    # ──────────────────────────────────────────────────────────────────────────

    def compute_loss(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """
        Mean Squared Error: MSE = mean( (y_pred - y_true)^2 )

        A perfect prediction gives MSE = 0.
        The further off the predictions, the higher the loss.
        MSE penalizes large errors heavily (because of the square).
        """
        return float(np.mean((y_pred - y_true) ** 2))

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 3 — Backward pass (Backpropagation)
    # ──────────────────────────────────────────────────────────────────────────

    def backward(self, y_true: np.ndarray):
        """
        Compute the gradient of the loss with respect to every weight.

        WHAT IS A GRADIENT?
            It tells us: "if I increase this weight by a tiny amount,
            does the loss go up or down, and by how much?"

        HOW?
            We use the chain rule from calculus, working backwards
            from the output layer to the input layer.

        dL/dW_i = dL/da_i * da_i/dz_i * dz_i/dW_i
                   (loss grad)  (activation grad)  (linear grad)

        After this call, self.grad_weights[i] and self.grad_biases[i]
        hold the gradient for layer i.

        Args:
            y_true: True values, shape (batch_size, 1)
        """
        n = y_true.shape[0]  # batch size — used to average the gradients

        self.grad_weights = [None] * len(self.weights)
        self.grad_biases  = [None] * len(self.biases)

        # ── Start at the output layer ────────────────────────────────────────
        # For MSE loss with linear output activation:
        #   dL/dz_output = 2 * (y_pred - y_true) / n
        # The "2" is the derivative of the square in MSE.
        delta = 2.0 * (self.activations[-1] - y_true) / n

        # ── Walk backwards through every layer ─────────────────────────────
        for i in reversed(range(len(self.weights))):

            # Gradient for weights:
            #   dL/dW_i = activation_input_to_this_layer.T  @  delta
            self.grad_weights[i] = self.activations[i].T @ delta

            # Gradient for biases:
            #   dL/db_i = sum of delta across the batch dimension
            self.grad_biases[i] = np.sum(delta, axis=0, keepdims=True)

            # Propagate delta further back (only if there's a layer below)
            if i > 0:
                # Pass error back through the weights of this layer
                delta = delta @ self.weights[i].T
                # Multiply by ReLU derivative (stops gradient where z was ≤ 0)
                delta = delta * self._relu_grad(self.z_values[i - 1])

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 4 — Weight update (Gradient Descent)
    # ──────────────────────────────────────────────────────────────────────────

    def _update_weights(self):
        """
        Adjust every weight slightly in the direction that reduces loss.

        Gradient Descent rule:
            W = W - learning_rate * dL/dW

        If dL/dW is positive, the weight is too large — decrease it.
        If dL/dW is negative, the weight is too small — increase it.
        learning_rate controls how big the adjustment step is.
        """
        for i in range(len(self.weights)):
            self.weights[i] -= self.lr * self.grad_weights[i]
            self.biases[i]  -= self.lr * self.grad_biases[i]

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 5 — Training loop
    # ──────────────────────────────────────────────────────────────────────────

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int | None = None,
        batch_size: int | None = None,
        val_data=None,
        verbose: bool = True,
    ) -> dict:
        """
        Train the neural network using mini-batch gradient descent.

        Args:
            X:
                Training feature matrix.

            y:
                Training target vector.

            epochs:
                Number of training epochs. If None, uses config.py value.

            batch_size:
                Mini-batch size. If None, uses config.py value.

            val_data:
                Optional tuple (X_val, y_val).

            verbose:
                Print training progress.

        Returns:
            Dictionary containing training history.
        """

        # ---------------------------------------------------------
        # Use default configuration if not explicitly provided
        # ---------------------------------------------------------
        if epochs is None:
            epochs = self.epochs

        if batch_size is None:
            batch_size = self.batch_size

        # ---------------------------------------------------------
        # Scale training features
        # ---------------------------------------------------------
        X = self.scaler.fit_transform(X)

        if val_data is not None:
            X_val, y_val = val_data
            X_val = self.scaler.transform(X_val)
            val_data = (X_val, y_val)

        n = X.shape[0]

        history = {
            "train_loss": [],
            "val_loss": [],
        }

        self.loss_history.clear()

        # ---------------------------------------------------------
        # Training Loop
        # ---------------------------------------------------------
        for epoch in range(epochs):

            # Shuffle samples every epoch
            permutation = np.random.permutation(n)

            X_shuffled = X[permutation]
            y_shuffled = y[permutation]

            batch_losses = []

            # ---------------- Mini-batches ----------------

            for start in range(0, n, batch_size):

                end = start + batch_size

                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]

                # Forward pass
                y_pred = self.forward(X_batch)

                # Compute loss
                loss = self.compute_loss(y_pred, y_batch)

                batch_losses.append(loss)

                # Backpropagation
                self.backward(y_batch)

                # Gradient update
                self._update_weights()

            # -----------------------------------------------------
            # End of Epoch
            # -----------------------------------------------------
            avg_loss = float(np.mean(batch_losses))

            history["train_loss"].append(avg_loss)

            self.loss_history.append(avg_loss)

            # Validation
            if val_data is not None:

                X_val, y_val = val_data

                val_pred = self.forward(X_val)

                val_loss = self.compute_loss(val_pred, y_val)

                history["val_loss"].append(float(val_loss))

                if val_loss < self.best_loss:
                    self.best_loss = val_loss

            # Logging
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
                        "Epoch %4d/%d | Train Loss: %.6f",
                        epoch + 1,
                        epochs,
                        avg_loss,
                    )

        self.is_fitted = True

        return history
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        **kwargs,
    ):
        """
        Alias for train() to follow the scikit-learn API.
        """

        return self.train(X, y, **kwargs)

    # ──────────────────────────────────────────────────────────────────────────
    # Inference
    # ──────────────────────────────────────────────────────────────────────────

    def predict(self, X: np.ndarray) -> np.ndarray:


        """
            Generate predictions using the trained MLP.

            Args:
                X:
                    Feature matrix of shape (n_samples, n_features)

            Returns:
                Predicted values with shape (n_samples, 1)
        """

        if not self.is_fitted:
            raise RuntimeError(
                "The model has not been trained yet. Call train() first."
            )

        # Apply the same scaling used during training
        X_scaled = self.scaler.transform(X)

        predictions = self.forward(X_scaled)

        return predictions

    # ──────────────────────────────────────────────────────────────────────────
    # Save & Load
    # ──────────────────────────────────────────────────────────────────────────

    def save_model(self, filepath: str) -> None:
        """
        Save the trained model to disk.

        This saves:
            - network architecture
            - weights
            - biases
            - training hyperparameters
            - fitted scaler parameters
        """

        if not self.is_fitted:
            raise RuntimeError(
                "Cannot save an untrained model."
            )

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
        """
        Load a previously trained MLP model.
        """

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

        model.scaler.set_params(
            model_data["scaler_mean"],
            model_data["scaler_std"],
        )

        model.is_fitted = True

        logger.info("MLP model loaded from %s", filepath)

        return model
