# `Chatbot from Scratch`

The goal of this project is to make a Keras, Tensorflow, or Pytorch implementation of a chatbot.
The basic idea is to start by setting up your training environment as described below and then training on various data sets. 
Later we want to use our code to implement a chatbot. This requires finding a suitable data set. 
The inspiration for this project is the tensorflow NMT project found at the following link: [here](https://github.com/tensorflow/nmt) 
Finally there was a great deep learning youtube series from Siraj Raval. 

# Tensorflow

When this project was in development, tensorflow was in 1.15.4, and since then it has moved to 2. The software in this repository relys on 1.15.4. Github does not like this. For this reason the tensorflow line has been commented out of the requirements.amd64.txt file. You may still need it, and should install it by hand.

# Organization
The folders and files in the project are organized in the following manor. 
The root directory of the project is called `awesome-chatbot`. 
In that folder are sub folders named `data`,  `model`, `raw`, `seq_2_seq`, `transformer`, and `saved`.
There are several script files in the main folder along side the folders mentioned above. 
These scripts all have names that start with the word `do_` . 
This is so that when the files are listed by the computer the scripts will all appear together. 
Below is a folder by folder breakdown of the project.

## OPENAI

Place Authentication code in file called: `~/bin/awesome-chatbot-openai.txt`

This file should contain the code issued by OpenAi for the Beta.
