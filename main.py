import sys

from PyQt5.QtGui import QIcon
from scipy.io.wavfile import read, write
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QStyle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy import signal


class SpectrogramWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SpectrogramWidget, self).__init__(parent)

        # Set window title
        self.setWindowTitle("PySpectrogram")

        # vars
        self.file_path = ""
        self.num_channels = 1
        self.window_length = 0

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

        # Create label for types of spectrogram selector
        self.type_label = QtWidgets.QLabel("Select type of spectrogram:")

        # Create a button group to hold the radio buttons
        self.radios_type = QtWidgets.QButtonGroup()

        # Create a radio button for 2 types of spectrogram
        self.radios = []
        radio_button = QtWidgets.QRadioButton("Narrow")
        self.radios.append(radio_button)
        self.radios_type.addButton(radio_button)
        radio_button = QtWidgets.QRadioButton("Wide")
        self.radios.append(radio_button)
        self.radios_type.addButton(radio_button)

        # Connect to update plot after selection
        for radio_button in self.radios:
            radio_button.clicked.connect(self.update_plot)

        # Set default value
        self.radios[0].setChecked(True)

        # Create a button group to hold the radio buttons
        self.radio_channels = QtWidgets.QButtonGroup()

        # Create a radio button for each channel
        self.radio_buttons = []
        for i in range(2):
            radio_button = QtWidgets.QRadioButton(f"Channel {i + 1}")
            self.radio_buttons.append(radio_button)
            self.radio_channels.addButton(radio_button)

        # Connect the clicked signal of the radio buttons to a slot that updates the plot
        for radio_button in self.radio_buttons:
            radio_button.clicked.connect(self.update_plot)

        # Set the first radio button to be checked by default
        self.radio_buttons[0].setChecked(True)

        # Second by default is turned off
        self.radio_buttons[1].setDisabled(True)

        # Create a label for the slider
        self.overlap_label = QtWidgets.QLabel("Select overlap percentage:")

        # Create a slider with a range from 0 to 100
        self.overlap_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.overlap_slider.setMinimum(0)
        self.overlap_slider.setMaximum(100)
        self.overlap_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.overlap_slider.setTickInterval(5)
        self.overlap_slider.setValue(10)

        # Create a spin box to display the current value of the slider
        self.box_overlap = QtWidgets.QSpinBox()
        self.box_overlap.setRange(0, 100)
        self.box_overlap.setSingleStep(1)
        self.box_overlap.setReadOnly(True)
        self.box_overlap.setButtonSymbols(2)
        self.box_overlap.setValue(10)

        # Connect the valueChanged signal of the slider to the setValue slot of the spin box
        self.overlap_slider.valueChanged.connect(self.box_overlap.setValue)

        # Connect the valueChanged signal of the slider to a slot that updates the plot
        self.overlap_slider.valueChanged.connect(self.update_plot)

        # Create label for drop-down
        self.color_label = QtWidgets.QLabel("Select color map:")

        # Create a drop-down list with some items
        self.color_dropdown = QtWidgets.QComboBox()
        self.color_dropdown.addItems(["viridis", "plasma", "inferno", "magma", "cividis", "coolwarm"])

        # Connect the currentIndexChanged signal of the dropdown to a slot that updates the plot
        self.color_dropdown.currentIndexChanged.connect(self.update_plot)

        # Create label for drop-down
        self.window_label = QtWidgets.QLabel("Select window type:")

        # Create a drop-down list with some items
        self.window_dropdown = QtWidgets.QComboBox()
        self.window_dropdown.addItems(["tukey", "triang", "parzen", "flattop", "exponential"])

        # Connect the currentIndexChanged signal of the dropdown to a slot that updates the plot
        self.window_dropdown.currentIndexChanged.connect(self.update_plot)

        # Create a matplotlib figure and canvas to display the spectrogram
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        # Make spinbox and slider side by side
        h1_layout = QtWidgets.QHBoxLayout()
        h1_layout.addWidget(self.overlap_label)
        h1_layout.addWidget(self.overlap_slider)
        h1_layout.addWidget(self.box_overlap)

        # Same with color selector
        h2_layout = QtWidgets.QHBoxLayout()
        h2_layout.addWidget(self.color_label)
        h2_layout.addWidget(self.color_dropdown)

        # Same with window selector
        h3_layout = QtWidgets.QHBoxLayout()
        h3_layout.addWidget(self.window_label)
        h3_layout.addWidget(self.window_dropdown)

        # Same with radio num channels selector
        rh1_layout = QtWidgets.QHBoxLayout()
        for radio in self.radio_buttons:
            rh1_layout.addWidget(radio)

        # Same with radio type of spectrogram selector
        rh2_layout = QtWidgets.QHBoxLayout()
        rh2_layout.addWidget(self.type_label)
        for radio in self.radios:
            rh2_layout.addWidget(radio)

        # Create a layout to hold the widgets
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.select_file_button)
        layout.addWidget(self.save_plot_button)
        layout.addWidget(self.canvas)
        layout.addLayout(rh1_layout)
        layout.addLayout(rh2_layout)
        layout.addLayout(h1_layout)
        layout.addLayout(h2_layout)
        layout.addLayout(h3_layout)

        # set main layout
        self.setLayout(layout)

    def select_file(self):
        # Show the file dialog and get the selected file
        if self.file_dialog.exec_():
            self.file_path = self.file_dialog.selectedFiles()[0]
            overlap = self.box_overlap.value()
            cmap = self.color_dropdown.currentText()
            # draw plot
            self.plot_spectrogram(overlap, cmap)
            self.save_plot_button.setEnabled(True)

    def update_plot(self):
        # Get the current values of the inputs
        overlap = self.box_overlap.value()
        cmap = self.color_dropdown.currentText()

        # Update plot
        self.plot_spectrogram(overlap, cmap)

    def plot_spectrogram(self, overlap, cmap):
        # If file not selected escape
        if self.file_path == "":
            return
        # Load the audio data from the selected file
        sample_rate, data = read(self.file_path)

        # check if this is stereo file
        if len(data.shape) > 1:
            # enable radio buttons to select which channel to show
            self.num_channels = 2
            self.radio_buttons[1].setDisabled(False)
            # set data to selected channel
            if self.radio_buttons[0].isChecked():
                data = data[:, 0]
            else:
                data = data[:, 1]
        else:
            # if file is mono, disable second button
            self.num_channels = 1
            self.radio_buttons[1].setDisabled(True)

        # Update window length
        if self.radios[0].isChecked():
            self.window_length = int(0.04 * sample_rate)
        else:
            self.window_length = int(0.012 * sample_rate)

        # Calculate overlap
        overlap = int((self.window_length * self.box_overlap.value() / 100))
        if self.window_length <= overlap:
            overlap = self.window_length - 1

        # Compute the spectrogram
        freqs, times, spectrogram = signal.spectrogram(data, sample_rate,
                                                       noverlap=overlap,
                                                       window=signal.get_window(self.window_dropdown.currentText(),
                                                                                self.window_length),
                                                       nperseg=self.window_length)
        spectrogram = 10 * np.log(spectrogram)

        # Clear the figure and plot the new spectrogram
        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        ax.pcolormesh(times, freqs, spectrogram, cmap=self.color_dropdown.currentText())
        # set labels
        ax.set_ylabel("Frequency (Hz)")
        ax.set_xlabel("Time (s)")

        # Update the canvas to display the new spectrogram
        self.canvas.draw()

    # Save plot to png in selected directory
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
