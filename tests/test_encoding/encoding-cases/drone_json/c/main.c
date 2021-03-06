#include <assert.h>
#include <stdio.h>

#include "drone_json_bp.h"

int main(void) {
    struct Drone drone = {0};

    drone.status = DRONE_STATUS_RISING;
    drone.position.longitude = 2000;
    drone.position.latitude = 2000;
    drone.position.altitude = 1080;
    drone.flight.pose.yaw = 4321;
    drone.flight.pose.pitch = 1234;
    drone.flight.pose.roll = 5678;
    drone.flight.acceleration[0] = -1001;
    drone.flight.acceleration[1] = 1002;
    drone.flight.acceleration[2] = 1003;
    drone.power.is_charging = false;
    drone.power.battery = 98;
    drone.propellers[0].id = 1;
    drone.propellers[0].direction = ROTATING_DIRECTION_CLOCK_WISE;
    drone.propellers[0].status = PROPELLER_STATUS_ROTATING;
    drone.network.signal = 15;
    drone.network.heartbeat_at = 1611280511628;
    drone.landing_gear.status = LANDING_GEAR_STATUS_FOLDED;

    char s[1024] = {0};
    JsonDrone(&drone, s);
    printf("%s", s);

    return 0;
}
