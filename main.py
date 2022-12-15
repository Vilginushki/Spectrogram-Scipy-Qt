import sys

from scipy.io.wavfile import read, write
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy import signal


class SpectrogramWidget(QtWidgets.QWidget):
    # noinspection PyTypeChecker
    def __init__(self, parent=None):
        super(SpectrogramWidget, self).__init__(parent)
        # vars
        self.file_path = ""
        self.num_channels = 1

        # Create a file dialog for the user to select an audio file
        self.file_dialog = QFileDialog()
        self.file_dialog.setFileMode(QFileDialog.ExistingFile)
        self.file_dialog.setNameFilter("Audio files (*.wav)")

        # Create a button to open the file dialog
        self.select_file_button = QtWidgets.QPushButton("Select file", self)
        self.select_file_button.clicked.connect(self.select_file)

        # Create a button to save plot to png
        self.save_plot_button = QtWidgets.QPushButton("Save plot as PNG", self)
        self.save_plot_button.clicked.connect(self.save_plot)
        self.save_plot_button.setEnabled(False)

        # Create a button group to hold the radio buttons
        self.button_group = QtWidgets.QButtonGroup()

        # Create a radio button for each channel
        self.radio_buttons = []
        for i in range(2):
            radio_button = QtWidgets.QRadioButton(f"Channel {i + 1}")
            self.radio_buttons.append(radio_button)
            self.button_group.addButton(radio_button)

        # Connect the clicked signal of the radio buttons to a slot that updates the plot
        for radio_button in self.radio_buttons:
            radio_button.clicked.connect(self.update_plot)

        # Set the first radio button to be checked by default
        self.radio_buttons[0].setChecked(True)

        # Second by default is turned off
        self.radio_buttons[1].setDisabled(True)

        # Create a label for the slider
        self.overlap_label = QtWidgets.QLabel("Select overlap:")

        # Create a slider with a range from 0 to 100
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(5)

        # Create a spin box to display the current value of the slider
        self.spin_box = QtWidgets.QSpinBox()
        self.spin_box.setRange(0, 100)
        self.spin_box.setSingleStep(1)
        self.spin_box.setReadOnly(True)
        self.spin_box.setButtonSymbols(2)

        # Connect the valueChanged signal of the slider to the setValue slot of the spin box
        self.slider.valueChanged.connect(self.spin_box.setValue)

        # Connect the valueChanged signal of the slider to a slot that updates the plot
        self.slider.valueChanged.connect(self.update_plot)

        # Create label for drop-down
        self.drop_label = QtWidgets.QLabel("Select color map:")

        # Create a drop-down list with some items
        self.dropdown = QtWidgets.QComboBox()
        self.dropdown.addItems(["viridis", "plasma", "inferno", "magma", "cividis", "coolwarm"])

        # Connect the currentIndexChanged signal of the dropdown to a slot that updates the plot
        self.dropdown.currentIndexChanged.connect(self.update_plot)

        # Create label for drop-down
        self.drop_label2 = QtWidgets.QLabel("Select window type:(WIP)")

        # Create a drop-down list with some items
        self.dropdown2 = QtWidgets.QComboBox()
        self.dropdown2.addItems(["tukey", "triang", "parzen"])  # boxcar nie dziala

        # Connect the currentIndexChanged signal of the dropdown to a slot that updates the plot
        self.dropdown2.currentIndexChanged.connect(self.update_plot)

        # Create a matplotlib figure and canvas to display the spectrogram
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        # Make spinbox and slider side by side
        h1_layout = QtWidgets.QHBoxLayout()
        h1_layout.addWidget(self.overlap_label)
        h1_layout.addWidget(self.slider)
        h1_layout.addWidget(self.spin_box)

        # Same with drop menu
        h2_layout = QtWidgets.QHBoxLayout()
        h2_layout.addWidget(self.drop_label)
        h2_layout.addWidget(self.dropdown)

        # Same with drop menu 2
        h3_layout = QtWidgets.QHBoxLayout()
        h3_layout.addWidget(self.drop_label2)
        h3_layout.addWidget(self.dropdown2)

        radioh_layout = QtWidgets.QHBoxLayout()
        # Same with radios
        for radio in self.radio_buttons:
            radioh_layout.addWidget(radio)

        # Create a layout to hold the widgets
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.select_file_button)
        layout.addWidget(self.save_plot_button)
        layout.addWidget(self.canvas)
        layout.addLayout(radioh_layout)
        layout.addLayout(h1_layout)
        layout.addLayout(h2_layout)
        layout.addLayout(h3_layout)

        self.setLayout(layout)

    def select_file(self):
        # Show the file dialog and get the selected file
        if self.file_dialog.exec_():
            self.file_path = self.file_dialog.selectedFiles()[0]
            overlap = self.spin_box.value()
            cmap = self.dropdown.currentText()
            self.plot_spectrogram(overlap, cmap)
            self.save_plot_button.setEnabled(True)

    def update_plot(self):
        # Get the current values of the inputs
        overlap = self.spin_box.value()
        cmap = self.dropdown.currentText()

        # Update plot
        self.plot_spectrogram(overlap, cmap)

    def plot_spectrogram(self, overlap, cmap):
        # If file not selected escape
        if self.file_path == "":
            return
        # Load the audio data from the selected file
        sample_rate, data = read(self.file_path)
        # librosa.load(self.file_path, mono=False)


        # check if this is stereo file
        if len(data.shape) > 1:
            self.num_channels = 2
            self.radio_buttons[1].setDisabled(False)
            if self.radio_buttons[0].isChecked():
                data = data[:, 0]
            else:
                data = data[:, 1]

        else:
            self.num_channels = 1
            self.radio_buttons[1].setDisabled(True)
        print(len(data))

        # Compute the spectrogram
        freqs, times, spectrogram = signal.spectrogram(data, sample_rate,
                                                       noverlap=int(self.slider.value()/2),
                                                       # noverlap=int(signal.get_window(self.dropdown2.currentText(), 350) * (self.slider.value() / 105)),
                                                       window=signal.get_window(self.dropdown2.currentText(), 350))

        try:
            spectrogram = 10 * np.log(spectrogram)
        except:
            print("Probably smt went wrong")

        # Clear the figure and plot the new spectrogram
        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        ax.pcolormesh(times, freqs, spectrogram, cmap=self.dropdown.currentText())
        ax.set_ylabel("Frequency (Hz)")
        ax.set_xlabel("Time (s)")

        # Update the canvas to display the new spectrogram
        self.canvas.draw()

    def save_plot(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                             "PNG Files (*.png)", options=options)
        if file_name:
            self.canvas.print_png(file_name)
            pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = SpectrogramWidget()
    widget.show()
    sys.exit(app.exec_())
