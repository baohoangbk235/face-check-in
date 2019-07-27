import os
import matplotlib.pyplot as plt
import numpy as np 
import pickle

image_count = []
count = 0
labels = []
labels2indexes = {}
image_dir = '/data/facereg/ABB/images'
for name in os.listdir(image_dir):
	image_count.append(len(os.listdir(os.path.join(image_dir, name))))
	labels.append(name)
	labels2indexes[name] = count
	count += 1

with open('labels2indexes.pkl','wb') as f:
	pickle.dump(labels2indexes,f)

with open('labels.pkl','wb') as f:
	pickle.dump(labels,f)

y_pos = np.arange(len(labels))
plt.bar(y_pos, image_count, align='center', alpha=0.5)
# plt.xticks(y_pos, user)
plt.ylabel('Image quantiteis')
plt.xlabel('Users')
plt.title('Image count of all users')

plt.savefig('foo.png')

