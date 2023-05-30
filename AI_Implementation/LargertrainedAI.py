def AND_train(net, input, label, optimizer, epochs=20000):
    all_losses = []

    for epoch in range(epochs): 
        y = net.forward(input)    # Inference using current weights
        loss = mseloss(y, label)      # Calculate MSE loss
        loss.backward()                       # Backpropogate through the loss gradiants   
        optimizer.step()                      # Update model weights 
        optimizer.zero_grad()                 # Remove current gradients for next iteration   
        all_losses.append(loss)               # Trace the loss

        if epoch % int(epochs/10) == 0:                 # print progress   
            print(f'Epoch: {epoch} completed')
    return all_losses, net
  
def AND_test(net, input):
    y = net(input)
    return y

from picarx import Picarx
from time import sleep
import matplotlib.pyplot as plt 
import numpy as np 
import torch
from torch import nn
import torch.optim as optim
import csv
#picar innit
px = Picarx()

class LineFollowerNN(nn.Module):
    def __init__(self):
        super(LineFollowerNN, self).__init__()
        self.layer1 = nn.Linear(3, 3) #linear transform on the 3 sensors
        self.nonlin = torch.heaviside
        self.layer2 = nn.Linear(3, 1) #3 output possibilities (left, straight, right)
        self.relu = nn.ReLU()

    def forward(self,x):        
        x = self.layer1(x)
        x = x.pow(2)        
        x = self.layer2(x)
        x = x.pow(2)        
        return x
    
    
def load_data(filename):
    with open(filename, 'r') as csvfile:
        datareader = csv.reader(csvfile)
        datarow = []
        data = []
        prelabel = []
        labels = []
        for row in datareader:
            # Convert the values to floats and scale to the range of -1 to 1
            
            for x in row[1:-1]:
                sensor_prime = (-1+ (2*(int(x) / 1550.0)))
                sensor_primed = round(sensor_prime, 4)
                datarow.append(sensor_primed)
            data.append(datarow)
            datarow = []
            
            sleep(0.01)
            # Load the corresponding label for the row
            if len(row) >1:
                if int(row[-1]) == 0:
                    
                    prelabel.append(0.5)
                elif int(row[-1]) == -1:
                    prelabel.append(0)
                else:
                    prelabel.append(1)
                labels.append(prelabel)
                prelabel = []
    print(data)
    print(labels)
    return data, labels


chain_net = LineFollowerNN()

w1 = +0.4
w2 = +1.0
nn.init.constant_(chain_net.layer1.weight, w1)
nn.init.constant_(chain_net.layer2.weight, w2)
train_data, train_labels = load_data('sensor_data.csv')
input = torch.Tensor(train_data)
target = torch.Tensor(train_labels)

mse_loss = nn.MSELoss()
optimizer = torch.optim.SGD(chain_net.parameters(), lr=0.1)


print("-"*100)
print("w1: ",chain_net.layer1.weight)
print("w2: ",chain_net.layer2.weight)


output =  chain_net(input)
loss = mse_loss(output, target)
#loss.backward()
optimizer.step()

print("-"*100)
#print('input: ', input)
print('output: ', output)
print('target: ', target)
print('loss: ', loss)
print('calc loss: ',(output-target).pow(2))

print("-"*100)
print("w1 grad: ", chain_net.layer1.weight.grad)
print("w2 grad: ", chain_net.layer2.weight.grad)
print("-"*100)
print("w1: ",chain_net.layer1.weight)
print("w2: ",chain_net.layer2.weight)

epochs = 20000
mseloss = nn.MSELoss() 
optimizer = torch.optim.SGD(chain_net.parameters(), lr=0.01, momentum=0.9)

print("="*20,"Training","="*20)
loss_list,trained_net = AND_train(chain_net,input,target,optimizer,epochs)
test_output = AND_test(trained_net, input)


print("="*20,"Testing","="*20)
for i in range(len(test_output)):
    print(input[i].data, target[i].data, test_output[i].data)

print("="*20,"Loss function","="*20)
# Plot the change of loss 
print(loss_list[1:])