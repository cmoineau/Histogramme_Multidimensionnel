import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import time
from STHOLES import Workload as w
import matplotlib.pyplot as plt

epochs = 100  # Number of training sessions
training_size = 0.30  # Percentage of the data used for training
batch_size = 128
learning_rate = 0.0002


def show_training_resume(history, epochs, train_size, test_size, training_time):
    train_loss = history.history['loss']
    train_acc = history.history['acc']
    validation_loss = history.history['val_loss']
    validation_acc = history.history['val_acc']
    xc = range(epochs)
    plt.title('Training session using ' + str(train_size) + ' data for training and ' + str(test_size) +
              ' for testing\nTime for training : ' + str(training_time) + ' seconds')
    plt.plot(xc, train_loss, label="Train loss")
    plt.plot(xc, train_acc, label="Train accuracy")
    plt.plot(xc, validation_acc, label="Validation accuracy")
    plt.plot(xc, validation_loss, label="Validation accuracy")
    plt.legend()
    plt.show()


if __name__ == '__main__':
    optimizer = Adam
    print('Loading data ...\n')

    path = "../DATA/fake_data.txt"
    att1 = []
    att2 = []
    att3 = []
    with open(path, "r") as f:
        for line in f:
            line = line.split(',')
            att1.append(float(line[0]))
            att2.append(float(line[1]))
            att3.append(float(line[2]))
    tab_attribut = np.array([att1, att2])
    workload = w.create_workload(tab_attribut, 0.1, 200)
    X = [[],[]]
    Y = []
    for k in workload:
        X[0].append(k[0][0])
        X[1].append(k[0][1])
        Y.append(k[1])

    print('End of loading !\nCreating train and test data !')
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=training_size)
    print('Size of the training input : (' + str(len(X_train)) + ", " + str(len(X_train[0])) + ')')
    print('Data are ready !')

    print("Creating model")
    m = Sequential()

    m.add(Dense(16, input_shape=(len(X_train[0]), len(X_train[0][0]))))
    m.add(Dense(1, activation='relu'))
    m.add(Dense(1, activation='softmax'))  # Here we create our output
    opt = optimizer(lr=learning_rate)
    m.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])

    start_time = time.time()
    history = m.fit(X_train, Y_train, epochs=epochs, validation_data=(X_test, Y_test), batch_size=batch_size)
    end_time = time.time()
    # visualizing losses and accuracy
    show_training_resume(history, epochs, len(X_train), len(X_test), end_time - start_time)


def create_model():
    """
    This function create a model using the library keras.
    :param optimizer: The function you wan to use as an optimizer, by default it's Adam
    :return: The model of a CNN
    """
    # Define the model structure
    print("Creating model")
    m = Sequential()
    m.add(Dense(5, input_shape=(len(X_train[0]), len(X_train[0][0])), activation='relu'))
    m.add(Dense(5, activation='relu'))
    m.add(Dense(1, activation='softmax'))  # Here we create our output
    opt = optimizer(lr=learning_rate)
    m.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])
    return m


def training_model(m, epochs=50):
    """
    outputs = ["H", "N", "D", "A"]  # Happy, Neutral, Depressed, Angry
    This function train the model m.
    :param m: the model to train
    :param epochs: number of training sessions (by default 50)
    :return: the model trained
    """
    start_time = time.time()
    history = m.fit(X_train, Y_train, epochs=epochs, validation_data=(X_test, Y_test), batch_size=batch_size)
    end_time = time.time()
    # visualizing losses and accuracy
    show_training_resume(history, epochs, len(X_train), len(X_test), end_time-start_time)
    return m

