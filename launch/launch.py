import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import TimerAction
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_path = get_package_share_directory('custom_control_key')
    urdf_file = os.path.join(pkg_path, 'urdf', 'robot.urdf')
    world_file = os.path.join(pkg_path, 'worlds', 'obstacle.world')
    slam_yaml = os.path.join(pkg_path, 'configs', 'slam_config.yaml')
    map_file = os.path.join(pkg_path, 'maps', 'my_saved_map.pgm')

    with open(urdf_file, 'r') as inf:
        urdf_info = inf.read()

    nav2_navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'navigation_launch.py')),
        launch_arguments={
            'use_sim_time': 'false',
            'params_file': os.path.join(get_package_share_directory('nav2_bringup'), 'params', 'nav2_params.yaml')
        }.items(),
    )
    ydlidar_launch_dir = os.path.join(
        get_package_share_directory('ydlidar_ros2_driver'), 
        'launch'
    )


    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': urdf_info,
                'use_sim_time': False  
            }]
        ),
	IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ydlidar_launch_dir, 'ydlidar_launch.py')
        )
    ),
	 Node(
	    package='micro_ros_agent',
   	    executable='micro_ros_agent',
    	    arguments=['serial', '--dev', '/dev/esp32_microros'],
	    output='screen'
	),
	Node(
	  package='custom_control_key',
	  executable = 'odom_broadcaster_node',
	  name = 'odom_broadcaster_node',
	  output='screen'
	  ),
        # SLAM Toolbox Node (Disabled to use Nav2)
       Node(
           package='slam_toolbox',
           executable='async_slam_toolbox_node',
           name='slam_toolbox',
           output='screen',
           parameters=[slam_yaml, {'use_sim_time': False}]
       )
    ])
