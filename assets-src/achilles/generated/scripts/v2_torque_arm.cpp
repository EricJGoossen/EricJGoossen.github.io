// Steps Achilles' demo two-link arm (examples/two_joint_arm.arow: same masses,
// centers of mass and inertias) with V2's own classes and V2's unmodified
// Plant::update(): no gravity, a constant torque on the shoulder, none on the
// elbow, 1 ms steps. Writes t,q_shoulder,q_elbow (rad, relative joint angles).
//
//   v2_torque <torque N*m> <seconds> <out.csv>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <memory>

#include "control/actuators/angular_actuator.hpp"
#include "control/plant.hpp"
#include "dynamics/joints/revolute_joint.hpp"

using namespace achilles;

namespace {
char kBase[] = "base";
char kUpper[] = "upper_arm";
char kFore[] = "forearm";
const geometry::Frame<control::Plant> kPlantFrame("arm");
const geometry::Frame<control::Plant> kWorldFrame("world");

// Inertia about the center of mass from the .arow's pivot-referenced values.
spatial::Inertia Body(double mass, double com_y, double ixx_o, double iyy_o) {
    Eigen::Matrix3d i_com = Eigen::Matrix3d::Zero();
    i_com(0, 0) = ixx_o - mass * com_y * com_y;
    i_com(1, 1) = iyy_o;
    i_com(2, 2) = ixx_o - mass * com_y * com_y;
    return {i_com, math::Vector(0, com_y, 0), mass};
}

double AngleAboutX(const spatial::Pose& pose) {
    const Eigen::Quaterniond& q = pose.orientation().mat();
    return 2.0 * std::atan2(q.x(), q.w());
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 4) {
        std::fprintf(stderr, "usage: v2_torque <torque> <seconds> <out.csv>\n");
        return 1;
    }
    const double torque = std::atof(argv[1]);
    const double seconds = std::atof(argv[2]);
    const double dt = 0.001;

    auto base = std::make_unique<dynamics::Link>(
        kBase, spatial::Inertia(Eigen::Matrix3d::Identity(), math::Vector::zero(), 1.0)
    );
    // shoulder: 1 kg, h = 0.3 -> CoM 0.3; Ixx = Izz = 0.18083, Iyy = 0.015
    auto upper = std::make_unique<dynamics::Link>(kUpper, Body(1.0, 0.3, 0.18083, 0.015));
    // elbow: 0.4 kg, h = 0.15 -> CoM 0.375; Ixx = Izz = 0.07238, Iyy = 0.00576
    auto fore = std::make_unique<dynamics::Link>(kFore, Body(0.4, 0.375, 0.07238, 0.00576));

    const math::UnitVector x_axis(1, 0, 0);
    auto shoulder = std::make_unique<dynamics::joints::RevoluteJoint>(
        "shoulder", *base, *upper, x_axis, spatial::Pose::identity(), spatial::Twist::identity()
    );
    auto elbow = std::make_unique<dynamics::joints::RevoluteJoint>(
        "elbow", *upper, *fore, x_axis, spatial::Pose::identity(), spatial::Twist::identity()
    );
    dynamics::joints::AbstractJoint* shoulder_ptr = shoulder.get();
    dynamics::joints::AbstractJoint* elbow_ptr = elbow.get();

    geometry::TransformTree transforms;
    transforms.addTransform(std::make_unique<geometry::Transform>(
        shoulder->frame(), upper->frame(), spatial::Pose::identity()
    ));
    transforms.addTransform(std::make_unique<geometry::Transform>(
        elbow->frame(), fore->frame(), spatial::Pose::identity()
    ));

    dynamics::JointTree tree;
    tree.addJoint(std::move(shoulder));
    tree.addJoint(std::move(elbow));

    auto shoulder_motor =
        std::make_unique<control::actuators::AngularActuator>(math::Vector(1, 0, 0), *shoulder_ptr);
    control::actuators::Actuator* motor_ptr = shoulder_motor.get();
    std::unordered_map<control::actuators::Actuator::Frame, std::unique_ptr<control::actuators::Actuator>>
        actuators;
    actuators.emplace(control::actuators::Actuator::Frame("shoulder_motor"), std::move(shoulder_motor));

    auto base_transform = std::make_unique<geometry::Transform>(
        kPlantFrame, base->frame(), spatial::Pose::identity()
    );
    auto world_transform = std::make_unique<geometry::Transform>(
        kWorldFrame, kPlantFrame, spatial::Pose::identity()
    );

    std::unordered_map<dynamics::Link::Frame, std::unique_ptr<dynamics::Link>> links;
    const dynamics::Link::Frame base_frame = base->frame();
    const dynamics::Link::Frame upper_frame = upper->frame();
    const dynamics::Link::Frame fore_frame = fore->frame();
    links.emplace(base_frame, std::move(base));
    links.emplace(upper_frame, std::move(upper));
    links.emplace(fore_frame, std::move(fore));

    control::Plant plant(
        "arm", std::move(transforms), std::move(tree), std::move(base_transform),
        std::move(world_transform), std::move(actuators), std::move(links)
    );

    std::FILE* out = std::fopen(argv[3], "w");
    std::fprintf(out, "t,q_shoulder,q_elbow\n");
    const long steps = std::lround(seconds / dt);
    for (long k = 0; k <= steps; ++k) {
        std::fprintf(out, "%.6f,%.9f,%.9f\n", k * dt, AngleAboutX(shoulder_ptr->position()),
                     AngleAboutX(elbow_ptr->position()));
        motor_ptr->applyEffort(torque);
        plant.update(dt);
    }
    std::fclose(out);
    return 0;
}
