// A C interface to Eric's four arm control laws, compiled unmodified from their
// repos, so a MuJoCo loop in Python can call them through ctypes.
//   v1 openarm_cartesian_control @3bf55b0  CartesianImpedance  (pure Cartesian)
//   v2 openarm_impedance_control @871d1e3  Impedance           (Cartesian gains mapped to joint space)
//   v3 openarm_impedance_control @eb8e13a  ImpedanceLaw        (Cartesian + null space)
//   v4 openarm_impedance_control @b517999  RobotModel          (gravity torque for pass-through)
#include <string>
#include <vector>
#include "openarm_cartesian_control/cartesian_impedance.hpp"
#include "openarm_impedance_control/impedance.hpp"
#include "openarm_impedance_control/impedance_law.hpp"
#include "openarm_impedance_control/robot_model.hpp"

using Eigen::Map;
using Eigen::VectorXd;
static std::vector<std::string> names(const char** j, int n) { return {j, j + n}; }
static std::vector<double> vec(const double* v, int n) { return {v, v + n}; }
static void out(const VectorXd& t, double* o) { for (int i = 0; i < t.size(); ++i) o[i] = t(i); }

extern "C" {
void* v1_new(const char* urdf, const char** j, int n, const char* ee, const double* lo, const double* hi,
             const double* wrench, const double* tau, int grav, int damp, int stiff) {
  return new openarm_cartesian_control::CartesianImpedance(urdf, names(j, n), ee, vec(lo, 3), vec(hi, 3),
      vec(wrench, 6), vec(tau, n), grav, damp, stiff);
}
void v1_gains(void* p, const double* k, const double* d) {
  auto* c = static_cast<openarm_cartesian_control::CartesianImpedance*>(p);
  c->setStiffness(vec(k, 6)); c->setDamping(vec(d, 6));
}
void v1_fk(void* p, const double* q, int n, double* pos, double* quat_wxyz) {
  auto* c = static_cast<openarm_cartesian_control::CartesianImpedance*>(p);
  c->initFK(Map<const VectorXd>(q, n));
  for (int i = 0; i < 3; ++i) pos[i] = c->getPose()(i);
  const auto& qu = c->getOrientation();
  quat_wxyz[0] = qu.w(); quat_wxyz[1] = qu.x(); quat_wxyz[2] = qu.y(); quat_wxyz[3] = qu.z();
}
void v1_control(void* p, const double* q, const double* dq, int n, const double* pos, const double* quat_wxyz, double* tau) {
  auto* c = static_cast<openarm_cartesian_control::CartesianImpedance*>(p);
  Eigen::Quaterniond qr(quat_wxyz[0], quat_wxyz[1], quat_wxyz[2], quat_wxyz[3]);
  out(c->computeControl(Map<const VectorXd>(q, n), Map<const VectorXd>(dq, n), Eigen::Vector3d(pos[0], pos[1], pos[2]),
                        qr, Eigen::Vector3d::Zero(), Eigen::Vector3d::Zero()), tau);
}

void* v2_new(const char* urdf, const char** j, int n, const char* ee, const double* tau, int grav, int damp, int stiff) {
  return new openarm_impedance_control::Impedance(urdf, names(j, n), ee, vec(tau, n), grav, damp, stiff);
}
void v2_gains(void* p, const double* k, const double* d) {
  auto* c = static_cast<openarm_impedance_control::Impedance*>(p);
  c->setStiffness(vec(k, 6)); c->setDamping(vec(d, 6));
}
void v2_control(void* p, const double* q, const double* dq, const double* qr, int n, double* tau) {
  auto* c = static_cast<openarm_impedance_control::Impedance*>(p);
  out(c->computeControl(Map<const VectorXd>(q, n), Map<const VectorXd>(dq, n), Map<const VectorXd>(qr, n),
                        VectorXd::Zero(n)), tau);
}

void* v3_new(const char* urdf, const char** j, int n, const char* ee, const double* tau, const double* wrench, int grav) {
  return new openarm_impedance_controller::ImpedanceLaw(urdf, names(j, n), ee, vec(tau, n), vec(wrench, 6), grav);
}
void v3_gains(void* p, const double* k, const double* d, const double* kn, const double* dn, int n) {
  auto* c = static_cast<openarm_impedance_controller::ImpedanceLaw*>(p);
  c->setCartesianStiffness(vec(k, 6)); c->setCartesianDamping(vec(d, 6));
  c->setNullspaceStiffness(vec(kn, n)); c->setNullspaceDamping(vec(dn, n));
}
void v3_control(void* p, const double* q, const double* dq, const double* qr, int n, double* tau) {
  auto* c = static_cast<openarm_impedance_controller::ImpedanceLaw*>(p);
  out(c->computeControl(Map<const VectorXd>(q, n), Map<const VectorXd>(dq, n), Map<const VectorXd>(qr, n),
                        VectorXd::Zero(n)), tau);
}

void* v4_new(const char* urdf, const char** j, int n, const char* ee) {
  return new openarm_impedance_controller::RobotModel(urdf, names(j, n), ee);
}
void v4_gravity(void* p, const double* q, int n, double* tau) {
  auto* c = static_cast<openarm_impedance_controller::RobotModel*>(p);
  out(c->gravityTorqueRT(Map<const VectorXd>(q, n)), tau);
}
}
