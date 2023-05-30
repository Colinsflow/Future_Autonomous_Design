def AND_train(net, input, label, optimizer, epochs=20000):
    all_losses = []

    for epoch in range(epochs): 
        y = net.forward(input_tensors)    # Inference using current weights
        loss = mseloss(y, label_tensors)      # Calculate MSE loss
        #loss.backward()                       # Backpropogate through the loss gradiants   
        optimizer.step()                      # Update model weights 
        optimizer.zero_grad()                 # Remove current gradients for next iteration   
        all_losses.append(loss)               # Trace the loss

        if epoch % int(epochs/10) == 0:                 # print progress   
            print(f'Epoch: {epoch} completed')
    return all_losses, net
  
def AND_test(net, input):
    y = net(input)
    return y


import torch
import torch.nn as nn
import matplotlib.pyplot as plt


class AND_Preceptron(nn.Module):
    def __init__(self):   
        """Initialize the layers of the model."""
        super(AND_Preceptron, self).__init__()
        self.layer1 = nn.Linear(2,1)  # Applies a linear transformation to the incoming data: y=Ax+b
        self.nonlin_1 = torch.heaviside
        # self.nonlin_1 =  nn.Sigmoid()
    def forward(self,x):        
        x = self.layer1(x)   #Applies the element-wise function f(x)=1/(1+exp(−x))
        x = self.nonlin_1(x,torch.tensor(0.))
        
        return x
    
and_net = AND_Preceptron()

# Train_data
input_tensors = torch.tensor([[0.0,0.0], [0.0,1.0],[1.0,0.0],[1.0,1.0]])
label_tensors = torch.tensor([[0.0],[0.0],[0.0],[1.0]])


epochs = 20000
mseloss = nn.MSELoss() 
optimizer = torch.optim.SGD(and_net.parameters(), lr=0.01, momentum=0.9)

print("="*20,"Training","="*20)
loss_list,trained_net = AND_train(and_net,input_tensors,label_tensors,optimizer,epochs)
test_output = AND_test(trained_net, input_tensors)


print("="*20,"Testing","="*20)
for i in range(len(test_output)):
    print(input_tensors[i].data, test_output[i].data)

print("="*20,"Loss function","="*20)
# Plot the change of loss 
plt.plot(loss_list)
plt.ylabel('Loss')
plt.show()