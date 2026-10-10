# 🤖 Avibot Documentation

> **Version:** 15-06-26 | **Platform:** ROS 2 Humble | **Drive:** Differential (2 wheels + castor)

---

## 🧭 Introduction

Avibot is a 2-wheeled differential drive robot with a castor wheel at the front. It is configured to run:

- **SLAM** (manual)
- **Nav2 navigation**

---

## 📦 Components

| #   | Component        | Details                                                      |
| --- | ---------------- | ------------------------------------------------------------ |
| 1   | Raspberry Pi 5   | 16 GB RAM, 128 GB SD card                                    |
| 2   | Microcontrollers | ESP32 (motor control, encoders, micro-ROS) and NodeMCU (IMU) |
| 3   | IMU              | MPU6050                                                      |
| 4   | LiDAR            | YDLidar T-mini Plus                                          |
| 5   | Encoders         | 2× OE-775                                                    |
| 6   | Motors           | 2× Orange motors                                             |
| 7   | Motor driver     | Cytron motor driver                                          |

---

## 🔁 Usual Procedure (every new terminal)

Every time you open a **new terminal**, follow these steps in order before running any `ros2` command.

### Step 1: Connect to the Wi-Fi and SSH into the Pi

Connect your machine to the `avibot` Wi-Fi network:

| Field    | Value        |
| -------- | ------------ |
| SSID     | `avibot`     |
| Password | `avibot1234` |

Then SSH in. The password is `avibot`.

```bash
ssh avibot@avibot.local
```

### Step 2: Enter the Docker container

First time in this session:

```bash
./start.bash
```

Container already running, and you need another terminal inside it:

```bash
./new.bash
```

---

## 🚀 Steps to Run the Bot

### 1. Connect the hardware

| Device | USB port        | Symlink created by udev |
| ------ | --------------- | ----------------------- |
| ESP32  | USB 3.0, bottom | `/dev/esp32_microros`   |
| LiDAR  | USB 3.0, top    | `/dev/ydlidar`          |
| Camera | Any port        | default - `/dev/video0` |

> The Pi renames serial ports **by physical port**, so plug each device into its assigned port. Swapping them swaps the names.

### 2. Launch

```bash
ros2 launch custom_control_key launch.py
```

This starts:

- robot state publisher
- micro-ROS agent
- SLAM
- ydlidar
- `odom_broadcaster` (node inside the `custom_control_key` package)

### 3. Reset the ESP32

After launching, press **RST** on the ESP32 and keep the robot **completely stationary** until it connects to the micro-ROS agent. It calibrates the IMU gyro at boot to remove drift.

### 4. Drive

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

---

## ⚙️ How It Works

### ESP32 firmware

1. Subscribes to `/cmd_vel` and converts it to left and right wheel speeds.
2. Runs the speeds through a PID loop using encoder feedback, then drives the motors.
3. Publishes odometry to `/odom_esp`.
4. Publishes debug data to `/actual_vel`.
5. Accepts live PID tuning on `/pid_gains`.

### Topics

| Topic         | Direction (ESP32) | Type       | Purpose                                 |
| ------------- | ----------------- | ---------- | --------------------------------------- |
| `/cmd_vel`    | subscribe         | `Twist`    | Target linear and angular velocity      |
| `/pid_gains`  | subscribe         | `Vector3`  | PID tuning (x = Kp, y = Ki, z = Kd)     |
| `/odom_esp`   | publish           | `Odometry` | Odometry with an empty timestamp        |
| `/actual_vel` | publish           | `Twist`    | Debug (gyro rate and accumulated angle) |

### odom_broadcaster node

Takes the data from `/odom_esp`, stamps it with the Pi's clock, and publishes it on `/odom`. It also broadcasts the `odom → base_footprint` transform.

---

## 🎛️ Tuning the PID

Example:

```bash
ros2 topic pub --once /pid_gains geometry_msgs/msg/Vector3 "{x: 180.0, y: 900.0, z: 1.0}"
```

> Gains are not saved. After an ESP32 reset they return to the values compiled into the firmware.

---

## 🐞 Debug

### Config file paths

Workspace root inside the container is `/ros2_ws`.

| Config     | Source path                                                | Installed path (what the launch file uses)                                                   |
| ---------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| SLAM       | `/ros2_ws/src/custom_control_key/configs/slam_config.yaml` | `/ros2_ws/install/custom_control_key/share/custom_control_key/configs/slam_config.yaml`      |
| YDLidar    | `<ydlidar_ros2_driver>/params/Tmini-Plus-SH.yaml`          | `$(ros2 pkg prefix ydlidar_ros2_driver)/share/ydlidar_ros2_driver/params/Tmini-Plus-SH.yaml` |
| Robot URDF | `/ros2_ws/src/custom_control_key/urdf/robot.urdf`          | `/ros2_ws/install/custom_control_key/share/custom_control_key/urdf/robot.urdf`               |

> The launch file reads the **installed** copies. After editing a source YAML, run `colcon build --packages-select custom_control_key` (or build once with `--symlink-install`) so the change takes effect.

### Test each part individually

Run each command in its own terminal (follow the [usual procedure](#-usual-procedure-every-new-terminal) first). Stop `launch.py` before running these, so nothing starts twice.

| Part                     | One-line start                                                                                                                                                                         |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Robot state publisher    | `ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$(cat /ros2_ws/install/custom_control_key/share/custom_control_key/urdf/robot.urdf)"`          |
| LiDAR                    | `ros2 launch ydlidar_ros2_driver ydlidar_launch.py`                                                                                                                                    |
| LiDAR with a custom YAML | `ros2 launch ydlidar_ros2_driver ydlidar_launch.py params_file:=/path/to/Tmini-Plus-SH.yaml`                                                                                           |
| micro-ROS agent          | `ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/esp32_microros -b 115200`                                                                                                  |
| Odom broadcaster         | `ros2 run custom_control_key odom_broadcaster_node`                                                                                                                                    |
| SLAM                     | `ros2 run slam_toolbox async_slam_toolbox_node --ros-args -r __node:=slam_toolbox --params-file /ros2_ws/install/custom_control_key/share/custom_control_key/configs/slam_config.yaml` |
| Teleop                   | `ros2 run teleop_twist_keyboard teleop_twist_keyboard`                                                                                                                                 |

## 📝 Notes

- After starting the micro-ROS agent, always press **RST** on the ESP32 to initialise the connection.
- The ESP32 has no command timeout (just like in /cmd_vel). It keeps driving at the last `/cmd_vel` until you send a zero command, so keep the robot off the floor or be ready to stop it.
- Keep the robot stationary during the gyro calibration (about 4 seconds after reset).
- ALWAYS colcon build only on the /ros2_ws/ directory to avoid creating copies of install/ build/ log/ ( if you find any in any other directory pls delete it)

### ⚠️ Laptop running ROS 2 Jazzy

The robot runs **ROS 2 Humble**. If your laptop natively has **ROS 2 Jazzy**, do not run `ros2` commands directly on the laptop while connected to the `avibot` network. Jazzy's DDS traffic on the same network corrupts Humble's data.

Instead, set up a **Docker container running ROS 2 Humble** on your laptop and run all `ros2` commands (RViz, teleop, topic echo, etc.) inside it.

**If you already ran any `ros2` command in Jazzy while on the same network**, stop the ROS 2 daemon on the laptop to fix the issue:

```bash
ros2 daemon stop
```
