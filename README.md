# Black Hole Solar System Simulator 🌌

An interactive **3D gravitational simulation** of the solar system, enhanced with **black hole dynamics** and real-time physics, built using Python, Pygame, and OpenGL.

---

## 🚀 Features

* 🌍 Real-time simulation of planetary motion (Earth, Mars, Jupiter)
* 🌌 Black hole interaction with chaotic gravitational effects
* ⚖️ Visualization of the **barycenter (center of mass)** between the Sun and the black hole
* 🧲 Dynamic **gravitational field deformation** using a 3D grid
* 🔄 Binary orbit system (Sun ↔ Black Hole)
* 🛰️ Orbital trails for tracking motion
* 🎮 Interactive camera (rotation, zoom)
* ⏱️ Adjustable simulation speed and pause system

---

## 🌌 Project Overview

This project simulates gravitational interactions between celestial bodies in a 3D environment, with a strong focus on **realistic astrophysical behavior**.

A key feature of the simulation is the visualization of the **barycenter (center of mass)** formed between the Sun and a black hole of comparable mass. Instead of one object orbiting the other, both bodies revolve around a shared center of mass — a phenomenon that would realistically occur if a black hole of solar mass entered our solar system.

As the black hole approaches:

* Planets with significantly smaller masses become unstable
* Their orbits become chaotic
* Many are eventually **absorbed by the black hole**

Meanwhile, the Sun and the black hole form a **binary system**, potentially orbiting their barycenter for extremely long periods.

Another important aspect of the project is the **visual representation of the gravitational field**.
The deformation of the 3D grid illustrates how massive bodies curve space, making gravitational intensity intuitive and visible.

---

## 🧠 Technologies Used

* Python
* Pygame
* PyOpenGL
* NumPy

---

## 🎯 What This Project Demonstrates

* 3D graphics rendering using OpenGL
* Physics simulation based on Newtonian gravity
* Vector-based motion and force calculations
* Real-time interactive systems
* Complex behaviors (chaotic motion, orbital dynamics, gravitational interactions)

---

## ⚙️ Installation

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Simulation

```bash
python main.py
```

---

## 🎮 Controls

* **Mouse drag** → rotate camera
* **Scroll** → zoom in/out
* **SPACE** → pause / resume
* **B** → toggle black hole
* **UP / DOWN** → change simulation speed
* **R** → reset simulation
* **ESC** → exit

---

## 📌 Future Improvements

* Add more planets (Venus, Saturn, etc.)
* Improve collision detection
* Add realistic textures for planets
* Add gravitational lensing effects
* Optimize performance for larger systems

---

## 📜 License

This project is licensed under the MIT License.

