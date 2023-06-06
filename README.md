# Autonomous RC Car with Cartesian Street Grid Navigation

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Usage](#usage)

## Introduction

The goal of this senior design project is to develop an autonomous RC car that can navigate through a Cartesian street grid. The car is equipped with the Picar-x kit by SunFounder, which is a versatile and user-friendly platform for building and programming RC cars. By adding a 9-axis IMU, dual wing IR sensors, and a wheel encoder, we enhance the car's capabilities for accurate motion sensing orientation.

## Features

- Autonomous navigation through a Cartesian street grid
- Real-time motion sensing and orientation detection using the 9-axis IMU
- Obstacle detection and avoidance using dual wing IR sensors
- User-friendly interface for controlling and monitoring the car
- Modular and extensible codebase for future enhancements

## Hardware Requirements

To replicate this project, you will need the following hardware components:

- [Picar-x kit by SunFounder](https://www.sunfounder.com/products/picar-x-kit)
- 9-axis IMU (e.g., MPU-9250)
- Dual wing IR sensors
- Wheel encoder
- Raspberry Pi Camera Module 3 Wide Lens
- Arduino RP2040 Connect (Use a more capable development board)
- Raspberry Pi (model 3 or later) with microSD card
- USB camera module (optional, for visual feedback)
- Power supply for the RC car and Raspberry Pi

## Software Requirements

The software requirements for this project are as follows:

- Python IDE (PyCharms, Thonny, VS Code) and Arduino IDE
- Create Google Firebase Database
- Python 3.7 or above
- Raspbian operating system for Raspberry Pi
- Pip install pyrebase to interface with Google Firebase's real-time database
- Pip install ArUco library and opencv for ArUco recognition
- Install other libraries associated with SunFounder HAT and other sensors

## Usage

1. Ensure all the hardware components are properly connected and powered.
2. Establish wifi and database connectivity for all development boards.
3. First, run the overhead camera code to detect the coordinates of the ArUco code on top of the car.
4. Second, run the GUI on a local machine to view the orientation and positioning of the car, as well as traffic lights.
5. Third, run the Autonomous RC car code.
6. Enter the car ID or ArUco ID associated with a car, and provide a destination or subsquare on the grid to navigate to.
7. The car will begin navigating the Cartesian street grid based on the sensor inputs and algorithms implemented in the code.
8. Use the provided user interface (if available) to monitor and control the car during operation.
9. Experiment with different configurations, algorithms, and code modifications to enhance the car's performance and capabilities.

