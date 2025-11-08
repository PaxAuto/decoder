#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from etsi_its_spatem_ts_msgs.msg import (
    SPATEM,
    IntersectionState,
    MovementState,
    MovementEvent
    )     
from custom_msgs.msg import DecoderInfo              # Custom message for simplified decoded output


class DecoderNode(Node):
    """Decoder Node — extracts useful SPATEM info and republishes as DecoderInfo."""

    def __init__(self):
        # Initialize the node with name 'decoder_node'
        super().__init__('decoder_node')

        # ---------------------------------------------------------
        # Subscriber: listens to SPATEM messages on topic '/spat'
        # ---------------------------------------------------------
        self.subscription = self.create_subscription(
            SPATEM,
            '/spat',
            self.spat_callback,
            10
        )

        # ---------------------------------------------------------
        # Publisher: sends simplified DecoderInfo messages
        # to topic '/decoder_info'
        # ---------------------------------------------------------
        self.publisher = self.create_publisher(DecoderInfo, '/decoder_info', 10)

        # ---------------------------------------------------------
        # Log: prints only one Decoder Node startup confirmation
        # ---------------------------------------------------------
        self.get_logger().info('✅ Decoder Node started!')

    # ==========================================================
    # Callback: triggered whenever a SPATEM message is received
    # ==========================================================
    def spat_callback(self, msg: SPATEM):
        # Extract list of intersections from SPATEM
        intersections = msg.spat.intersections.array

        # Loop through each intersection inside SPATEM
        for intersection in intersections:
            intersection:IntersectionState = intersection
            # Extract intersection ID and name 
            intersection_id = intersection.id.id
            intersection_name = intersection.name.value

            # Loop through each signal group (traffic light group) within intersection
            for states in intersection.states.array:
                states:MovementState = states
                signal_group = states.signal_group.value

                # Loop through each event (signal phase)
                for event in states.state_time_speed.array:
                    event:MovementEvent = event
                    # Extract the event state (e.g., RED, GREEN, YELLOW)
                    event_state = event.event_state.value
                    
                    # ---------------------------------------------
                    # Create and populate DecoderInfo message
                    # ---------------------------------------------
                    msg_out = DecoderInfo()
                    msg_out.intersection_id = int(intersection_id)
                    msg_out.signal_group = int(signal_group)
                    msg_out.event_state = int(event_state)
                    msg_out.intersection_name = str(intersection_name)

                    # Publish the decoded info
                    self.publisher.publish(msg_out)


# ==========================================================
# Main entrypoint of the node
# ==========================================================
def main(args=None):
    # Initialize ROS 2 communication
    rclpy.init(args=args)

    # Create instance of DecoderNode
    node = DecoderNode()

    try:
        # Keep node active and spinning
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Gracefully stop the node when user interrupts
        pass

    # Destroy node and shutdown ROS
    node.destroy_node()
    rclpy.shutdown()


# Run the node
if __name__ == '__main__':
    main()
