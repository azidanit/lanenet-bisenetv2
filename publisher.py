import socket
# import rospy
# from std_msgs.msg import Int32 

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(("127.0.0.1",5005))
# distancePub = rospy.Publisher('right_camera/trotoar/distance',Int32)
# distanceSMAPub = rospy.Publisher('right_camera/trotoar/distanceSMA',Int32)

# rospy.init_node('rightCamera')
# rate = rospy.Rate(10)
while True:
    distance,addr = sock.recvfrom(1024)
    tmp = str(distance)
    # distancePub.publish(tmp[2:6])
    # distanceSMAPub.publish(tmp[7:11)
    print("distance %s" % tmp[2:6])
    print("distanceSMA %s" % tmp[7:11])