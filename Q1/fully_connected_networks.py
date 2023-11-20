"""
Implements fully connected networks in PyTorch.
WARNING: you SHOULD NOT use ".to()" or ".cuda()" in each implementation block.
"""
import torch
from libs import Solver


class Linear(object):

    @staticmethod
    def forward(x, w, b):
        """
        Computes the forward pass for an linear (fully-connected) layer.
        The input x has shape (N, d_1, ..., d_k) and contains a minibatch of N
        examples, where each example x[i] has shape (d_1, ..., d_k). We will
        reshape each input into a vector of dimension D = d_1 * ... * d_k, and
        then transform it to an output vector of dimension M.
        Inputs:
        - x: A tensor containing input data, of shape (N, d_1, ..., d_k)
        - w: A tensor of weights, of shape (D, M)
        - b: A tensor of biases, of shape (M,)
        Returns a tuple of:
        - out: output, of shape (N, M)
        - cache: (x, w, b)
        """
        out = None
        N = x.shape[0]
        x_reshaped = x.view(N, -1)  
        out = torch.matmul(x_reshaped, w.to(x_reshaped.dtype)) + b
        cache = (x, w, b)
        return out, cache

    @staticmethod
    def backward(dout, cache):
        """
        Computes the backward pass for an linear layer.
        Inputs:
        - dout: Upstream derivative, of shape (N, M)
        - cache: Tuple of:
          - x: Input data, of shape (N, d_1, ... d_k)
          - w: Weights, of shape (D, M)
          - b: Biases, of shape (M,)
        Returns a tuple of:
        - dx: Gradient with respect to x, of shape
          (N, d1, ..., d_k)
        - dw: Gradient with respect to w, of shape (D, M)
        - db: Gradient with respect to b, of shape (M,)
        """
        x, w, b = cache
        dx, dw, db = None, None, None
        N = x.shape[0]
        dx = torch.matmul(dout.to(w.t().dtype), w.t())
        dx = dx.view(x.shape)
        x_reshaped = x.view(N, -1)
        dw = torch.matmul(x_reshaped.t().to(dout.dtype), dout)
        db = torch.sum(dout, dim=0)
        return dx, dw, db


class ReLU(object):

    @staticmethod
    def forward(x):
        """
        Computes the forward pass for a layer of rectified
        linear units (ReLUs).
        Input:
        - x: Input; a tensor of any shape
        Returns a tuple of:
        - out: Output, a tensor of the same shape as x
        - cache: x
        """
        out = None
        out = torch.relu(x)
        cache = x
        return out, cache

    @staticmethod
    def backward(dout, cache):
        """
        Computes the backward pass for a layer of rectified
        linear units (ReLUs).
        Input:
        - dout: Upstream derivatives, of any shape
        - cache: Input x, of same shape as dout
        Returns:
        - dx: Gradient with respect to x
        """
        dx, x = None, cache
        dx = dout * (cache > 0).float()
        return dx


class Linear_ReLU(object):

    @staticmethod
    def forward(x, w, b):
        """
        Convenience layer that performs an linear transform
        followed by a ReLU.

        Inputs:
        - x: Input to the linear layer
        - w, b: Weights for the linear layer
        Returns a tuple of:
        - out: Output from the ReLU
        - cache: Object to give to the backward pass (hint: cache = (fc_cache, relu_cache))
        """
        out = None
        cache = None
        linear_out, fc_cache = Linear.forward(x, w, b)
        relu_out, relu_cache = ReLU.forward(linear_out)
        cache = (fc_cache, relu_cache)
        return relu_out, cache


    @staticmethod
    def backward(dout, cache):
        """
        Backward pass for the linear-relu convenience layer
        """
        dx, dw, db = None, None, None
        drelu = ReLU.backward(dout, cache[1])
        dx, dw, db = Linear.backward(drelu, cache[0])
        return dx, dw, db


def softmax_loss(x, y):
    """
    Computes the loss and gradient for softmax classification.
    Inputs:
    - x: Input data, of shape (N, C) where x[i, j] is the score for
      the jth class for the ith input.
    - y: Vector of labels, of shape (N,) where y[i] is the label
      for x[i] and 0 <= y[i] < C
    Returns a tuple of:
    - loss: Scalar giving the loss
    - dx: Gradient of the loss with respect to x
    """
    loss = None
    dx = None
    N = x.shape[0]
    # x_shifted = x - torch.max(x, dim=1, keepdim=True)[0]
    exp_func = torch.exp(x)
    Probability = exp_func / torch.sum(exp_func, dim=1, keepdim=True)
    loss = -torch.log(Probability[range(N), y]).sum() / N
    dx = Probability.clone()
    dx[range(N), y] =  dx[range(N), y] - 1
    dx = dx/N
    return loss, dx


class TwoLayerNet(object):
    """
    A two-layer fully-connected neural network with ReLU nonlinearity and
    softmax loss that uses a modular layer design. We assume an input dimension
    of D, a hidden dimension of H, and perform classification over C classes.
    The architecure should be linear - relu - linear - softmax.
    Note that this class does not implement gradient descent; instead, it
    will interact with a separate Solver object that is responsible for running
    optimization.

    The learnable parameters of the model are stored in the dictionary
    self.params that maps parameter names to PyTorch tensors.
    """

    def __init__(self, input_dim=3*32*32, hidden_dim=100, num_classes=10,
                 weight_scale=1e-3, reg=0.0,
                 dtype=torch.float32, device='cpu'):
        """
        Initialize a new network.
        Inputs:
        - input_dim: An integer giving the size of the input
        - hidden_dim: An integer giving the size of the hidden layer
        - num_classes: An integer giving the number of classes to classify
        - weight_scale: Scalar giving the standard deviation for random
          initialization of the weights.
        - reg: Scalar giving L2 regularization strength.
        - dtype: A torch data type object; all computations will be
          performed using this datatype. float is faster but less accurate,
          so you should use double for numeric gradient checking.
        - device: device to use for computation. 'cpu' or 'cuda'
        """
        self.params = {}
        self.reg = reg
        self.params['W1'] = torch.normal(0, weight_scale, dtype = dtype,size = (input_dim, hidden_dim))
        self.params['W2'] = torch.normal(0, weight_scale, dtype = dtype,size = (hidden_dim, num_classes))
        self.params['b1'] = torch.zeros(hidden_dim, dtype=dtype, device=device)
        self.params['b2'] = torch.zeros(num_classes, dtype = dtype, device = device)
        for i in self.params:
            self.params[i] = self.params[i].type(dtype).to(device)

    def save(self, path):
        checkpoint = {
          'reg': self.reg,
          'params': self.params,
        }
        torch.save(checkpoint, path)
        print("Saved in {}".format(path))

    def load(self, path, dtype, device):
        checkpoint = torch.load(path, map_location='cpu')
        self.params = checkpoint['params']
        self.reg = checkpoint['reg']
        for p in self.params:
            self.params[p] = self.params[p].type(dtype).to(device)
        print("load checkpoint file: {}".format(path))

    def loss(self, X, y=None):
        """
        Compute loss and gradient for a minibatch of data.

        Inputs:
        - X: Tensor of input data of shape (N, d_1, ..., d_k)
        - y: int64 Tensor of labels, of shape (N,). y[i] gives the
          label for X[i].

        Returns:
        If y is None, then run a test-time forward pass of the model
        and return:
        - scores: Tensor of shape (N, C) giving classification scores,
          where scores[i, c] is the classification score for X[i]
          and class c.
        If y is not None, then run a training-time forward and backward
        pass and return a tuple of:
        - loss: Scalar value giving the loss
        - grads: Dictionary with the same keys as self.params, mapping
          parameter names to gradients of the loss with respect to
          those parameters.
        """
        scores = None
        out_hid, cache_hid = Linear_ReLU.forward(X, self.params['W1'], self.params['b1'])
        scores, cache_scores = Linear.forward(out_hid, self.params['W2'], self.params['b2'])
        # If y is None then we are in test mode so just return scores
        if y is None:
            return scores
        loss, grads = 0, {}
        
        loss, dscores = softmax_loss(scores, y)
        reg_loss = self.reg * (torch.sum(self.params['W1'] ** 2) + torch.sum(self.params['W2'] ** 2))
        loss = loss + reg_loss
        dout_hid, dw2, db2 = Linear.backward(dscores, cache_scores)
        dx, dw1, db1 = Linear_ReLU.backward(dout_hid, cache_hid)
        dw1 = dw1 + 2 * self.reg * self.params['W1']
        dw2 = dw2 + 2 * self.reg * self.params['W2']
        grads['W1'] = dw1
        grads['W2'] = dw2
        grads['b1'] = db1
        grads['b2'] = db2

        return loss, grads


class FullyConnectedNet(object):
    """
    A fully-connected neural network with an arbitrary number of hidden layers,
    ReLU nonlinearities, and a softmax loss function.
    For a network with L layers, the architecture will be:

    {linear - relu - [dropout]} x (L - 1) - linear - softmax

    where dropout is optional, and the {...} block is repeated L - 1 times.

    Similar to the TwoLayerNet above, learnable parameters are stored in the
    self.params dictionary and will be learned using the Solver class.
    """

    def __init__(self, hidden_dims, input_dim=3*32*32, num_classes=10,
                 dropout=0.0, reg=0.0, weight_scale=1e-2, seed=None,
                 dtype=torch.float, device='cpu'):
        """
        Initialize a new FullyConnectedNet.

        Inputs:
        - hidden_dims: A list of integers giving the size of each
          hidden layer.
        - input_dim: An integer giving the size of the input.
        - num_classes: An integer giving the number of classes to classify.
        - dropout: Scalar between 0 and 1 giving the drop probability
          for networks with dropout. If dropout=0 then the network
          should not use dropout.
        - reg: Scalar giving L2 regularization strength.
        - weight_scale: Scalar giving the standard deviation for random
          initialization of the weights.
        - seed: If not None, then pass this random seed to the dropout
          layers. This will make the dropout layers deteriminstic so we
          can gradient check the model.
        - dtype: A torch data type object; all computations will be
          performed using this datatype. float is faster but less accurate,
          so you should use double for numeric gradient checking.
        - device: device to use for computation. 'cpu' or 'cuda'
        """
        self.use_dropout = dropout != 0
        self.reg = reg
        self.num_layers = 1 + len(hidden_dims)
        self.dtype = dtype
        self.params = {}

        layer_dimen = [input_dim] + hidden_dims + [num_classes]
        for i in range(self.num_layers):
            w = torch.normal(0, weight_scale, dtype=dtype,size=(layer_dimen[i], layer_dimen[i + 1])).to(device)
            b = torch.zeros(layer_dimen[i + 1], dtype=dtype, device=device)
            self.params[f'W{i + 1}'] = w
            self.params[f'b{i + 1}'] = b

        # When using dropout we need to pass a dropout_param dictionary
        # to each dropout layer so that the layer knows the dropout
        # probability and the mode (train / test). You can pass the same
        # dropout_param to each dropout layer.
        self.dropout_param = {}
        if self.use_dropout:
            self.dropout_param = {'mode': 'train', 'p': dropout}
            if seed is not None:
                self.dropout_param['seed'] = seed

    def save(self, path):
        checkpoint = {
          'reg': self.reg,
          'dtype': self.dtype,
          'params': self.params,
          'num_layers': self.num_layers,
          'use_dropout': self.use_dropout,
          'dropout_param': self.dropout_param,
        }

        torch.save(checkpoint, path)
        print("Saved in {}".format(path))

    def load(self, path, dtype, device):
        checkpoint = torch.load(path, map_location='cpu')
        self.params = checkpoint['params']
        self.dtype = dtype
        self.reg = checkpoint['reg']
        self.num_layers = checkpoint['num_layers']
        self.use_dropout = checkpoint['use_dropout']
        self.dropout_param = checkpoint['dropout_param']

        for p in self.params:
            self.params[p] = self.params[p].type(dtype).to(device)

        print("load checkpoint file: {}".format(path))

    def loss(self, X, y=None):
        """
        Compute loss and gradient for the fully-connected net.
        Input / output: Same as TwoLayerNet above.
        """
        X = X.to(self.dtype)
        mode = 'test' if y is None else 'train'

        # Set train/test mode for batchnorm params and dropout param
        # since they behave differently during training and testing.
        if self.use_dropout:
            self.dropout_param['mode'] = mode
        scores = None

        caches = []
        scores = X
        for i in range(self.num_layers):
            if i == self.num_layers - 1:
                scores, cache = Linear.forward(scores, self.params[f'W{i + 1}'],self.params[f'b{i + 1}'])
            else:
                scores, cache = Linear_ReLU.forward(scores, self.params[f'W{i + 1}'],self.params[f'b{i + 1}'])
            caches.append(cache)

        # If test mode return early
        if mode == 'test':
            return scores

        loss, grads = 0.0, {}
        loss, dout = softmax_loss(scores, y)
        for i in range(self.num_layers):
            reg_loss_ = 0.5 * self.reg * torch.sum(self.params[f'W{i + 1}'] ** 2)
            loss = loss + reg_loss_
        for i in range(self.num_layers - 1, -1, -1):
            cache = caches[i]
            if i == self.num_layers - 1:
                dout, dw, db = Linear.backward(dout, cache)
            else:
                dout, dw, db = Linear_ReLU.backward(dout, cache)
            dw = dw + self.reg * self.params[f'W{i + 1}']
            grads[f'W{i + 1}'] = dw
            grads[f'b{i + 1}'] = db
        return loss, grads


def create_solver_instance(data_dict, dtype, device):
    model = TwoLayerNet(hidden_dim=100, dtype=dtype, device=device)
    solver = None
    solver = Solver(model, data_dict, optim_config={'learning_rate': 0.5,},
            lr_decay=0.95,
            num_epochs=70, batch_size=500,
            print_every=1000,
            device=device)
    # solver.train()
    return solver


def get_three_layer_network_params():
    ###############################################################
    # TODO: Change weight_scale and learning_rate so your         #
    # model achieves 100% training accuracy within 20 epochs.     #
    ###############################################################
    weight_scale = 0.1   # Experiment with this!
    learning_rate = 0.2  # Experiment with this!
    ################################################################
    #                             END OF YOUR CODE                 #
    ################################################################
    return weight_scale, learning_rate


def get_five_layer_network_params():
    ################################################################
    # TODO: Change weight_scale and learning_rate so your          #
    # model achieves 100% training accuracy within 20 epochs.      #
    ################################################################
    learning_rate = 0.2  # Experiment with this!
    weight_scale = 0.1   # Experiment with this!
    ################################################################
    #                       END OF YOUR CODE                       #
    ################################################################
    return weight_scale, learning_rate


def sgd(w, dw, config=None):
    """
    Performs vanilla stochastic gradient descent.
    config format:
    - learning_rate: Scalar learning rate.
    """
    if config is None:
        config = {}
    config.setdefault('learning_rate', 1e-2)

    w -= config['learning_rate'] * dw
    return w, config


def sgd_momentum(w, dw, config=None):
    """
    Performs stochastic gradient descent with momentum.
    config format:
    - learning_rate: Scalar learning rate.
    - momentum: Scalar between 0 and 1 giving the momentum value.
      Setting momentum = 0 reduces to sgd.
    - velocity: A numpy array of the same shape as w and dw used to
      store a moving average of the gradients.
    """
    if config is None:
        config = {}
    config.setdefault('learning_rate', 1e-2)
    config.setdefault('momentum', 0.9)
    v = config.get('velocity', torch.zeros_like(w))

    next_w = None
    v = config['momentum'] * v - config['learning_rate'] * dw
    next_w = w + v
    config['velocity'] = v

    return next_w, config


def rmsprop(w, dw, config=None):
    """
    Uses the RMSProp update rule, which uses a moving average of squared
    gradient values to set adaptive per-parameter learning rates.
    config format:
    - learning_rate: Scalar learning rate.
    - decay_rate: Scalar between 0 and 1 giving the decay rate for the squared
      gradient cache.
    - epsilon: Small scalar used for smoothing to avoid dividing by zero.
    - cache: Moving average of second moments of gradients.
    """
    if config is None:
        config = {}
    config.setdefault('learning_rate', 1e-2)
    config.setdefault('decay_rate', 0.99)
    config.setdefault('epsilon', 1e-8)
    config.setdefault('cache', torch.zeros_like(w))

    next_w = None
    next_w = w - config['learning_rate'] * dw / torch.sqrt(config['cache'] + config['epsilon'])
    config['cache'] = config['decay_rate'] * config['cache'] + (1 - config['decay_rate']) * dw ** 2
    return next_w, config


def adam(w, dw, config=None):
    """
    Uses the Adam update rule, which incorporates moving averages of both the
    gradient and its square and a bias correction term.
    config format:
    - learning_rate: Scalar learning rate.
    - beta1: Decay rate for moving average of first moment of gradient.
    - beta2: Decay rate for moving average of second moment of gradient.
    - epsilon: Small scalar used for smoothing to avoid dividing by zero.
    - m: Moving average of gradient.
    - v: Moving average of squared gradient.
    - t: Iteration number.
    """
    if config is None:
        config = {}
    config.setdefault('learning_rate', 1e-3)
    config.setdefault('beta1', 0.9)
    config.setdefault('beta2', 0.999)
    config.setdefault('epsilon', 1e-8)
    config.setdefault('m', torch.zeros_like(w))
    config.setdefault('v', torch.zeros_like(w))
    config.setdefault('t', 0)

    next_w = None
    config['m'] = config['beta1'] * config['m'] + (1 - config['beta1']) * dw
    config['v'] = config['beta2'] * config['v'] + (1 - config['beta2']) * (dw ** 2)
    config['t'] = config['t'] + 1
    m_hat = config['m'] / (1 - config['beta1'] ** config['t'])
    v_hat = config['v'] / (1 - config['beta2'] ** config['t'])
    next_w = w - config['learning_rate'] * m_hat / (torch.sqrt(v_hat) + config['epsilon'])

    return next_w, config


class Dropout(object):

    @staticmethod
    def forward(x, dropout_param):
        """
        Performs the forward pass for (inverted) dropout.
        Inputs:
        - x: Input data: tensor of any shape
        - dropout_param: A dictionary with the following keys:
          - p: Dropout parameter. We *drop* each neuron output with
            probability p.
          - mode: 'test' or 'train'. If the mode is train, then
            perform dropout;
          if the mode is test, then just return the input.
          - seed: Seed for the random number generator. Passing seed
            makes this
            function deterministic, which is needed for gradient checking
            but not in real networks.
        Outputs:
        - out: Tensor of the same shape as x.
        - cache: tuple (dropout_param, mask). In training mode, mask
          is the dropout mask that was used to multiply the input; in
          test mode, mask is None.
        NOTE: Please implement **inverted** dropout, not the vanilla
              version of dropout.
        See http://cs231n.github.io/neural-networks-2/#reg for more details.
        NOTE 2: Keep in mind that p is the probability of **dropping**
                a neuron output; this might be contrary to some sources,
                where it is referred to as the probability of keeping a
                neuron output.
        """
        p, mode = dropout_param['p'], dropout_param['mode']
        if 'seed' in dropout_param:
            torch.manual_seed(dropout_param['seed'])

        mask = None
        out = None
        if mode == 'train':
            mask = (torch.rand_like(x) > p).float()
            mask = mask / (1-p)
            out = x * mask
        elif mode == 'test':
            out = x
        cache = (dropout_param, mask)

        return out, cache

    @staticmethod
    def backward(dout, cache):
        """
        Perform the backward pass for (inverted) dropout.
        Inputs:
        - dout: Upstream derivatives, of any shape
        - cache: (dropout_param, mask) from Dropout.forward.
        """
        dropout_param, mask = cache
        mode = dropout_param['mode']

        dx = None
        if mode == 'train':
            dx = dout * mask
        elif mode == 'test':
            dx = dout
        return dx

