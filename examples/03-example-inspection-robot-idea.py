

from navigation import NavDNN
net = NavDNN()

while True:
    arr = pipeline.cameras[0].image
    img = Image.fromarray(arr)
    theta = net(img) 
    vehicle.set_steering(theta)