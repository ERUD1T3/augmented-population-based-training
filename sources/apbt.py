############################################################
#   Dev: Josias Moukpe
#   Class: Machine Learning
#   Assginment: Term Paper
#   Date: 4/10/2022
#   file: apbt.py
#   Description: main class for the augmented 
#   population based training algorithm
#############################################################

# imports
from ann import ANN
import random
from copy import deepcopy

# Augmentated Population Based Training
class APBT:
    '''
    Augmentated Population Based Training
    Builts on top of Deepmind PBT algorithm
    and augments it to also optimize the 
    Neural network arcthiecture
    '''
    
    def __init__(
        self, 
        k, 
        end_training,
        training, 
        testing, 
        attributes, 
        debug):
        '''
        Initialize the APBT class
        '''
        self.k = k # min = 20
        self.population = [None for _ in range(k)]
        self.hyperparams = [None for _ in range(k)]
        self.perfs = [0.0 for _ in range(k)]
        self.last_ready = [0 for _ in range(k)]
        self.epochs = end_training
        self.debug = debug

        # reading attributes 
        self.attributes, self.in_attr, self.out_attr = self.read_attributes(attributes) 
        # reading input,output lenght
        self.input_units, self.output_units = self.get_input_output_len()
        # reading data
        self.training = self.read_data(training)
        self.testing = self.read_data(testing)
        self.n_examples = len(self.training)
        # setting validation to 20% of the training data
        self.validation = self.training[:int(self.n_examples * 0.2)]
        self.training = self.training[int(self.n_examples * 0.2):]

        # initial ranges for the constants
        self.LR_RANGE = (1e-4, 1e-1) # learning rate
        self.M_RANGE = (.0, .9) # momentum
        self.D_RANGE = (.0, .1) # decay
        self.HL_RANGE = (1, 4) # hidden layers
        self.HUPL_RANGE = (2, 10) # hidden units per layer
        self.PERTS = (0.8, 1.2) # perturbations
        self.READINESS = 10 # number of epochs to wait before exploitation
        self.TRUNC = .2 # truncation threshold
        self.X, self.Y = 1e3, 1e-3
        # generate the population
        self.generate_population(k)

        # best running best performer, its performance,
        # and its hyperparameters 
        self.best = None


        if self.debug:
            print('Population:', self.population)
            print('Hyperparams:', self.hyperparams)
            print('Perfs:', self.perfs)
            print('last_ready:', self.last_ready)
            print('Training:', self.training)
            print('validation:', self.validation)
            print('Testing:', self.testing)
            print('Number of examples:', self.n_examples)

    def read_attributes(self, attr_path):
        '''
        Read in the attributes
        '''
        attributes = {}
        in_attr, out_attr = [], []
        is_input = True

            # read in the attributes
        with open(attr_path, 'r') as f:
            for line in f:
                if len(line) > 1:
                    words = line.strip().split()
                    
                    # storing the attributes
                    attributes[words[0]] = words[1:]

                    # storing the input attributes
                    if is_input:
                        in_attr.append(words[0])
                    else:
                        out_attr.append(words[0])
                    # order.append(words[0])
                else:
                    is_input = False

        if self.debug:
            print('Attributes: ', attributes)
            print('Input attributes: ', in_attr)
            print('Output attributes: ', out_attr)

        if len(attributes) == 0:
            raise Exception('No attributes found')


        return attributes, in_attr, out_attr

    def to_encode(self, attr):
        '''
        Return true if the value is discrete
        to encode
        '''
        values = self.attributes[attr]
        # encode the values
        if len(values) > 1:
            if values[0] == '0' and values[1] == '1':
                return False
            else:
                return True
        else:
            return False

    def onehot(self, attr, value):
        '''
        Preprocess to convert a data instance 
        to one-of-n/onehot encoding
        '''
        # get the index of the value
        encoded = [0.0 for _ in range(len(self.attributes[attr]))]
        encoded[self.attributes[attr].index(value)] = 1.0

        return encoded

    def read_data(self, data_path):
        '''
        Read in the training data and testing data
        '''
        data = []

        # read in the attributes
        with open(data_path, 'r') as f:
            for line in f:
                if len(line) > 0:
                    items = line.strip().split()
                    # get items iterator
                    items_iter = iter(items)

                    In, Out = [],[]
                    # get inputs
                    for attr in self.in_attr:
                        value = next(items_iter)
                        if self.to_encode(attr):
                            # encode discrete values
                            encoded = self.onehot(attr, value)
                            In += encoded # since encoded is a list
                        else:
                            # encode continuous values
                            In.append(float(value))

                    # get outputs
                    for attr in self.out_attr:
                        value = next(items_iter)
                        if self.to_encode(attr):
                            # encode discrete values
                            encoded = self.onehot(attr, value)
                            Out += encoded # since encoded is a list
                        else:
                            # encode continuous values
                            Out.append(float(value))

                    # check if the encoding should be applied
                    # when encoding applied, update the input or output units sizes
                    data.append([In, Out])

        if len(data) == 0:
            raise Exception('No data found')

        return data

    def decode(self, attr, encoded):
        '''
        Decode the encoded value
        '''
        # get the index of the value
        # value = self.attributes[attr][encoded.index(1.0)]
        if self.debug:
            print('Encoded: ', encoded)
            print('attr: ', attr)
            print('Attributes: ', self.attributes[attr])
        value_encoded = zip(self.attributes[attr], encoded)
        # sort the encoded value
        sorted_encoded = sorted(value_encoded, key=lambda x: x[1], reverse=True)

        # get the value
        value = sorted_encoded[0][0]

        if self.debug:
            print('Decoded: ', value)
            print('Sorted encoded: ', sorted_encoded)

        return value

    def get_input_output_len(self):
        '''
        Get the input and output units
        '''
        # getting total number of input units
        input_units = 0
        for attr in self.in_attr:
            values = self.attributes[attr]
            # check specifically for identity
            if values[0] == '0' and values[1] == '1':
                input_units += 1
            else:
                input_units += len(values)

        # getting total number of output units  
        output_units = 0
        for attr in self.out_attr:
            values = self.attributes[attr]
            # check specifically for identity
            if values[0] == '0' and values[1] == '1':
                output_units += 1
            else:
                output_units += len(values)

        return input_units, output_units

    def generate_net(self, idx):
        '''
        Generate a new network
        '''
        h = {
            # 'k_fold': random.randint(2, 10),
            'learning_rate': random.uniform(*self.LR_RANGE),
            'momentum': random.uniform(*self.M_RANGE),
            'decay': random.uniform(*self.D_RANGE),
            'hidden_units': [
                random.randint(*self.HUPL_RANGE) 
                for _ in range(random.randint(*self.HL_RANGE))
            ] # list of number of nodes in each layer
        }

        net = ANN(
            net_id=idx,
            hyperparams=h, 
            input_units=self.input_units,
            output_units=self.output_units,
            debug=self.debug
        )

        return net, h
       

    def generate_population(self, population_size):
        '''
        Generate the population of neural networks
        '''
        for n in range(population_size):
            net, h = self.generate_net(n)
            self.population[n] = net
            self.hyperparams[n] = h


    def step(self, net, hyperparams):
        '''
        Apply one optimization step to the network,
        given the hyperparameters
        '''
        net.set_hyperparameters(hyperparams)
        net.training_step(self.training)
        return net

    def evaluate(self, net):
        '''
        Evaluate the performance of the network
        '''
        size = net.num_params()
        accuracy = net.test(self.validation)
        perf = self.X * accuracy + self.Y * size
        print(f' | perf: {perf:.3f} | size: {size} | accuracy: {accuracy:.3f}', end='\n')
        return perf

    # TODO: test 
    def exploit(self, net, hyperparams, perf):
        '''
        Exploit the rest of the population 
        to find a better solution
        truncation selection
        '''
        # get index of net
        index = self.perfs.index(perf)

        # sort the population by perfs
        sorted_nets = [i for i in range(self.k)]
        sorted_nets.sort(key=lambda x: self.perfs[x], reverse=True)

        top = self.TRUNC # top 20%
        bottom = 1 - self.TRUNC # bottom 20%

        # check if net is in the bottom 20%
        if index in sorted_nets[int(self.k * bottom):]:
            # get the index of one of the top 20%
            top_index = random.choice(sorted_nets[:int(self.k * top)])
            # get the index of the top net
            top_net = deepcopy(self.population[top_index])
            # get the hyperparameters of the top net
            top_hyperparams = deepcopy(self.hyperparams[top_index])
            # replace the current net with the top net
            return top_net, top_hyperparams
        else :
            # net is not in the bottom 20%
            # so it's doing okay for now
            return net, hyperparams


    # TODO: test
    def explore(self, net, hyperparams):
        '''
        Produce new hyperparameters to explore by 
        perturbing the current hyperparameters
        '''
        # randomly perturb the hyperparameters by factor
        hyperparams['learning_rate'] *= random.choice([*self.PERTS])
        hyperparams['momentum'] *= random.choice([*self.PERTS])
        hyperparams['decay'] *= random.choice([*self.PERTS])

        # randomly perturb the topology
        rng_index = random.randint(1, len(net.topology) - 2)
        # randomly add or remove a unit
        rng_choice = random.choice([-1, 1])
        # udpated the hyperparameter
        hyperparams['hidden_units'][rng_index] += rng_choice

        # adjust the weights based on changed topology
        if rng_choice == -1:
            # remove weight associated with removed unit
            # choose a random unit to remove
            rng_unit = random.randint(0, net.topology[rng_index] - 1)
            # row weight
            net.weights[f'W{rng_index}{rng_index-1}'].remove(rng_unit)
            # column weight
            for r in range(net.topology[rng_index+1]):
                net.weights[f'W{rng_index+1}{rng_index}'][r].remove(rng_unit)
            # remove the unit
            net.topology[rng_index] -= 1

        else: # rng_choice = 1
            # row weight
            net.weights[f'W{rng_index}{rng_index-1}'].append([
                net.rand_init() for _ in range(1+net.topology[rng_index-1])])
            # column weight
            for r in range(net.topology[rng_index+1]):
                net.weights[f'W{rng_index+1}{rng_index}'][r].append(net.rand_init())
            # add the unit
            net.topology[rng_index] += 1            

        return net, hyperparams

    # TODO: test
    def is_ready(self, last_ready, timestep):
        '''
        Check if the net is ready to exploit and explore
        after a certain number of last_ready since last ready
        '''
        # checking the readiness
        if timestep - last_ready > self.READINESS:
            # might need to check if the performance is good enough
            return True
        # by default not ready
        return False
            

    # TODO: test
    def is_diff(sel, net1, net2):
        '''
        Check if the networks are different
        '''
        # check if the weights are different
        return net1.weights != net2.weights


    # TODO: test
    def train(self):
        '''
        Train the network population
        '''
        for e in range(self.epochs):
            # print the epoch number
            print('Epoch: ', e, end='\n')
            for i in range(self.k):
                # getting a net of the population
                net = self.population[i]
                hyperparams = self.hyperparams[i]
                perf = self.perfs[i]
                last = self.last_ready[i]
                # optimize the net
                net = self.step(net, hyperparams)
                # evaluate the net
                perf = self.evaluate(net)

                # check if the net is ready to exploit and explore
                if self.is_ready(last, e):
                    new_net, new_hyperparams = self.exploit(net, hyperparams, perf)
                    # check if the new network is different
                    if self.is_diff(new_net, net):
                        net, hyperparams = self.explore(new_net, new_hyperparams)
                        perf = self.evaluate(net)

                # update the population
                self.population[i] = net
                self.hyperparams[i] = hyperparams
                self.perfs[i] = perf
                self.last_ready[i] = last + 1
            
            # get best net so far 
            self.best = self.get_best()

            # print the best net so far
            print(f'Current best net perf: {self.best[1]:.2f}', end='\n')
            print(f'Current best net hyperparameters: {self.best[2]}', end='\n')
            
        # return net with the best performance
        best_perf = max(self.perfs)
        best_net = self.population[self.perfs.index(best_perf)]
        hyperparams = self.hyperparams[self.perfs.index(best_perf)]
        # check if the best net is better than best known net
        if best_perf > self.best[1]:
            self.best = (best_net, best_perf, hyperparams)

        return self.best
        
    def get_best(self):
        '''
        Get the best net
        '''
        # max gen  performance
        best_perf = max(self.perfs)
        if not self.best or self.best[1] < best_perf: # if no best net yet or new best net found
            best_net = self.population[self.perfs.index(best_perf)]
            best_hyperparams = self.hyperparams[self.perfs.index(best_perf)]
            return best_net, best_perf, best_hyperparams
        else: # best net is the same
            return self.best