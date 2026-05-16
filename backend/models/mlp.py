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
import os


class MLP:

    def __init__(self, input_size: int, hidden_sizes: list, learning_rate: float = 0.001):
        """
        Build the network and randomly initialize all weights.

        Args:
            input_size:    Number of input features (len(FEATURE_COLS))
            hidden_sizes:  List of neuron counts per hidden layer, e.g. [64, 32]
            learning_rate: How large a step to take each weight update.
                           Too high → training diverges.
                           Too low  → training is very slow.

        Example: MLP(10, [64, 32]) creates:
            Layer 0: 10  → 64  (weights shape 10×64)
            Layer 1: 64  → 32  (weights shape 64×32)
            Layer 2: 32  → 1   (weights shape 32×1 — the output)
        """
        self.lr = learning_rate
        self.layer_sizes = [input_size] + hidden_sizes + [1]  # 1 output neuron

        self.weights = []
        self.biases  = []

        for i in range(len(self.layer_sizes) - 1):
            n_in  = self.layer_sizes[i]
            n_out = self.layer_sizes[i + 1]

            # He initialization: weights ~ Normal(0, sqrt(2 / n_in))
            # WHY? If weights are too large, signals explode through layers.
            # If too small, signals vanish. He init keeps them in a good range
            # specifically for ReLU activations.
            w = np.random.randn(n_in, n_out) * np.sqrt(2.0 / n_in)
            b = np.zeros((1, n_out))  # biases start at zero

            self.weights.append(w)
            self.biases.append(b)

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

    def train(self, X: np.ndarray, y: np.ndarray,
              epochs: int = 1000, batch_size: int = 16,
              val_data=None, verbose: bool = True) -> dict:
        """
        Full training loop: repeat forward → loss → backward → update.

        MINI-BATCHING explained:
            Instead of feeding all data at once (slow) or one sample at a time
            (noisy), we feed small "batches" of 16 samples. This gives a good
            balance of speed and gradient accuracy.

        Args:
            X:          Training features,  shape (n_samples, n_features)
            y:          Training targets,   shape (n_samples, 1)
            epochs:     How many full passes through the training data
            batch_size: Samples per mini-batch
            val_data:   Optional (X_val, y_val) for tracking validation loss
            verbose:    Print progress every 200 epochs

        Returns:
            dict with "train_loss" list (and "val_loss" if val_data given)
        """
        n       = X.shape[0]
        history = {"train_loss": [], "val_loss": []}

        for epoch in range(epochs):

            # Shuffle training data every epoch.
            # WHY? To prevent the model from learning the order of the data.
            perm       = np.random.permutation(n)
            X_shuffled = X[perm]
            y_shuffled = y[perm]

            batch_losses = []

            # Mini-batch loop
            for start in range(0, n, batch_size):
                X_batch = X_shuffled[start : start + batch_size]
                y_batch = y_shuffled[start : start + batch_size]

                y_pred = self.forward(X_batch)          # Step 1
                loss   = self.compute_loss(y_pred, y_batch)  # Step 2
                batch_losses.append(loss)
                self.backward(y_batch)                  # Step 3
                self._update_weights()                  # Step 4

            avg_loss = float(np.mean(batch_losses))
            history["train_loss"].append(avg_loss)

            # Compute validation loss (no weight update here — just measuring)
            if val_data is not None:
                X_val, y_val = val_data
                val_pred = self.forward(X_val)
                val_loss = self.compute_loss(val_pred, y_val)
                history["val_loss"].append(val_loss)

            if verbose and (epoch + 1) % 200 == 0:
                val_str = f"  |  Val loss: {val_loss:.6f}" if val_data else ""
                print(f"  Epoch {epoch + 1:>4}/{epochs}  |  Train loss: {avg_loss:.6f}{val_str}")

        return history

    # ──────────────────────────────────────────────────────────────────────────
    # Inference
    # ──────────────────────────────────────────────────────────────────────────

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Generate predictions for new data (no gradient storage needed).
        Just runs the forward pass.
        """
        return self.forward(X)

    # ──────────────────────────────────────────────────────────────────────────
    # Save & Load
    # ──────────────────────────────────────────────────────────────────────────

    def save(self, path: str):
        """
        Save all weights, biases, and architecture to a .npz file.
        .npz is NumPy's native compressed archive format.
        """
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

        save_dict = {
            "layer_sizes": np.array(self.layer_sizes),
            "lr":          np.array([self.lr]),
        }
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            save_dict[f"w_{i}"] = w
            save_dict[f"b_{i}"] = b

        np.savez(path, **save_dict)
        print(f"  MLP saved → {path}")

    @classmethod
    def load(cls, path: str) -> "MLP":
        """Reconstruct an MLP from a saved .npz file."""
        data        = np.load(path)
        layer_sizes = data["layer_sizes"].tolist()
        lr          = float(data["lr"][0])

        input_size   = layer_sizes[0]
        hidden_sizes = layer_sizes[1:-1]  # everything except input and output

        model = cls(input_size, hidden_sizes, lr)
        for i in range(len(model.weights)):
            model.weights[i] = data[f"w_{i}"]
            model.biases[i]  = data[f"b_{i}"]

        print(f"  MLP loaded ← {path}")
        return model
