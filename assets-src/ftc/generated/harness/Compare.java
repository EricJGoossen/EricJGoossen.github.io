import java.io.*;
import java.util.*;

/**
 * Runs Road Runner 1.0.1 (core, from source), Pedro Pathing 3.0.2 (core, from source) and SKIDADDLE
 * (1584b3b) unchanged on one simulated FTC mecanum robot and writes each run's trace.
 *
 * The robot: heading held at 0, so field and robot axes agree. Each axis is a DC-motor model,
 * a = (power * VFREE - v) / TAU, with the wheel powers normalized like a mecanum drive (|forward| + |strafe| <= 1),
 * each wheel's acceleration capped at the tyres' grip (|ax| + |ay| <= ATRAC), and zero power coasting on friction (MU), like FLOAT mode.
 */
public class Compare {
    static final double VFREE = 75, TAU = 0.5, ATRAC = 50, MU = 10, DT = 0.01;
    static final double VMAX = Double.parseDouble(System.getProperty("vmax","50")), AMAX = Double.parseDouble(System.getProperty("amax","50"));                    // the limits every follower is given

    // ------------------------------------------------------------------ the robot
    static class Robot {
        double x, y, vx, vy, f, s; boolean brake;
        void power(double fw, double st, boolean br) {
            double n = Math.max(1, Math.abs(fw) + Math.abs(st));
            f = fw / n; s = st / n; brake = br;
        }
        void step(double dt) {
            double ax, ay;
            if (Math.abs(f) < 1e-9 && Math.abs(s) < 1e-9) {
                if (brake) { ax = -vx / TAU; ay = -vy / TAU; }
                else {
                    double sp = Math.hypot(vx, vy);
                    if (sp < MU * dt) { vx = vy = 0; ax = ay = 0; }
                    else { ax = -MU * vx / sp; ay = -MU * vy / sp; }
                }
            } else { ax = (f * VFREE - vx) / TAU; ay = (s * VFREE - vy) / TAU; }
            double a = Math.abs(ax) + Math.abs(ay);                       // each wheel's grip: |ax| + |ay| <= ATRAC
            if (a > ATRAC) { ax *= ATRAC / a; ay *= ATRAC / a; }
            vx += ax * dt; vy += ay * dt; x += vx * dt; y += vy * dt;
        }
    }

    // ------------------------------------------------------------------ scenarios
    /** A path: a cubic Bezier (four control points) or, with poly set, straight lines through the points. */
    static class Scenario {
        String name; double[] cp; double vx0, vy0; boolean poly;
        Scenario(String n, double[] c, double vx, double vy) { name = n; cp = c; vx0 = vx; vy0 = vy; }
        Scenario polyline() { poly = true; return this; }
        double ex() { return cp[cp.length - 2]; }
        double ey() { return cp[cp.length - 1]; }
        /** Dense points along the path, for measuring how far the robot strays from it. */
        double[][] samples() {
            List<double[]> out = new ArrayList<>();
            if (!poly) for (int i = 0; i < 2000; i++) {
                double t = i / 1999.0;
                out.add(new double[] {BezierInternal.d(cp[0], cp[2], cp[4], cp[6], t)[0], BezierInternal.d(cp[1], cp[3], cp[5], cp[7], t)[0]});
            } else for (int k = 0; k + 3 < cp.length; k += 2) for (int i = 0; i <= 1000; i++) {
                double t = i / 1000.0;
                out.add(new double[] {cp[k] + t * (cp[k + 2] - cp[k]), cp[k + 1] + t * (cp[k + 3] - cp[k + 1])});
            }
            return out.toArray(new double[0][]);
        }
    }

    static class Trace {
        String follower, scenario; double precomputeMs; List<double[]> rows = new ArrayList<>(); String note = "";
    }

    // ------------------------------------------------------------------ Road Runner
    static class BezierInternal implements com.acmerobotics.roadrunner.PositionPath<com.acmerobotics.roadrunner.Internal> {
        final double[] c;
        BezierInternal(double[] c) { this.c = c; }
        static double[] d(double p0, double p1, double p2, double p3, double t) {
            double u = 1 - t;
            return new double[] {
                u*u*u*p0 + 3*u*u*t*p1 + 3*u*t*t*p2 + t*t*t*p3,
                3*u*u*(p1-p0) + 6*u*t*(p2-p1) + 3*t*t*(p3-p2),
                6*u*(p2-2*p1+p0) + 6*t*(p3-2*p2+p1),
                6*(p3-3*p2+3*p1-p0) };
        }
        public com.acmerobotics.roadrunner.Vector2dDual<com.acmerobotics.roadrunner.Internal> get(double t, int n) {
            double[] dx = d(c[0], c[2], c[4], c[6], t), dy = d(c[1], c[3], c[5], c[7], t);
            double[] xs = new double[n], ys = new double[n];
            for (int i = 0; i < n; i++) { xs[i] = i < 4 ? dx[i] : 0; ys[i] = i < 4 ? dy[i] : 0; }
            return new com.acmerobotics.roadrunner.Vector2dDual<>(
                new com.acmerobotics.roadrunner.DualNum<>(xs), new com.acmerobotics.roadrunner.DualNum<>(ys));
        }
        public double length() { return 1.0; }
        public com.acmerobotics.roadrunner.Vector2dDual<com.acmerobotics.roadrunner.Internal> begin(int n) { return get(0, n); }
        public com.acmerobotics.roadrunner.Vector2dDual<com.acmerobotics.roadrunner.Internal> end(int n) { return get(1, n); }
    }

    static double RR_POS = 8, RR_VEL = 0;

    static com.acmerobotics.roadrunner.MinVelConstraint rrVel() {
        return new com.acmerobotics.roadrunner.MinVelConstraint(List.of(
            new com.acmerobotics.roadrunner.MecanumKinematics(15.0).new WheelVelConstraint(VMAX),
            new com.acmerobotics.roadrunner.AngularVelConstraint(Math.PI)));
    }

    /** Road Runner's own builder: strafeTo each corner, constant heading. It splits at each corner and stops there. */
    static List<com.acmerobotics.roadrunner.TimeTrajectory> rrBuild(Scenario sc) {
        if (!sc.poly) return List.of(rrBuild(sc.cp));
        var b = new com.acmerobotics.roadrunner.TrajectoryBuilder(
            new com.acmerobotics.roadrunner.TrajectoryBuilderParams(1e-6, new com.acmerobotics.roadrunner.ProfileParams(0.25, 0.1, 1e-2)),
            new com.acmerobotics.roadrunner.Pose2d(sc.cp[0], sc.cp[1], 0), 0.0, rrVel(),
            new com.acmerobotics.roadrunner.ProfileAccelConstraint(-AMAX, AMAX));
        for (int k = 2; k + 1 < sc.cp.length; k += 2) b = b.strafeTo(new com.acmerobotics.roadrunner.Vector2d(sc.cp[k], sc.cp[k + 1]));
        List<com.acmerobotics.roadrunner.TimeTrajectory> out = new ArrayList<>();
        for (var t : b.build()) out.add(new com.acmerobotics.roadrunner.TimeTrajectory(t));
        return out;
    }

    static com.acmerobotics.roadrunner.TimeTrajectory rrBuild(double[] cp) {
        var pos = new com.acmerobotics.roadrunner.ArclengthReparamCurve2d(new BezierInternal(cp), 1e-6);
        var pose = new com.acmerobotics.roadrunner.HeadingPosePath(pos,
            new com.acmerobotics.roadrunner.ConstantHeadingPath(com.acmerobotics.roadrunner.Rotation2d.exp(0.0), pos.length()));
        var mapped = new com.acmerobotics.roadrunner.MappedPosePath(pose, new com.acmerobotics.roadrunner.IdentityPoseMap());
        var prof = com.acmerobotics.roadrunner.Profiles.profile(
            new com.acmerobotics.roadrunner.ProfileParams(0.25, 0.1, 1e-2), mapped, 0.0,
            rrVel(), new com.acmerobotics.roadrunner.ProfileAccelConstraint(-AMAX, AMAX));
        var traj = new com.acmerobotics.roadrunner.Trajectory(mapped, prof, List.of(0.0, pos.length()));
        return new com.acmerobotics.roadrunner.TimeTrajectory(traj);
    }

    static Trace runRR(Scenario sc, double maxT) {
        Trace tr = new Trace(); tr.follower = "Road Runner"; tr.scenario = sc.name;
        for (int i = 0; i < 20; i++) rrBuild(sc);                      // warm up the JIT
        long t0 = System.nanoTime(); int reps = 20;
        List<com.acmerobotics.roadrunner.TimeTrajectory> tts = null;
        for (int i = 0; i < reps; i++) tts = rrBuild(sc);
        tr.precomputeMs = (System.nanoTime() - t0) / 1e6 / reps;
        var ctl = new com.acmerobotics.roadrunner.HolonomicController(RR_POS, RR_POS, 0, RR_VEL, RR_VEL, 0);
        var ff = new com.acmerobotics.roadrunner.MotorFeedforward(0, 1 / VFREE, TAU / VFREE);
        Robot r = new Robot(); r.x = sc.cp[0]; r.y = sc.cp[1]; r.vx = sc.vx0; r.vy = sc.vy0;
        double total = 0; for (var x : tts) total += x.duration;
        for (double t = 0; t < maxT; t += DT) {
            double tl = t; int k = 0;                                       // run the trajectories back to back
            while (k < tts.size() - 1 && tl > tts.get(k).duration) { tl -= tts.get(k).duration; k++; }
            var tt = tts.get(k);
            var target = tt.get(Math.min(tl, tt.duration));
            var cmd = ctl.compute(target, new com.acmerobotics.roadrunner.Pose2d(r.x, r.y, 0),
                new com.acmerobotics.roadrunner.PoseVelocity2d(new com.acmerobotics.roadrunner.Vector2d(r.vx, r.vy), 0));
            double fx = ff.compute(cmd.linearVel.x), fy = ff.compute(cmd.linearVel.y);
            r.power(fx, fy, false);
            r.step(DT);
            tr.rows.add(new double[] {t + DT, r.x, r.y, r.vx, r.vy});
        }
        tr.note = String.format(Locale.US, "%d trajectories, %.2f s planned", tts.size(), total);
        return tr;
    }

    // ------------------------------------------------------------------ Pedro Pathing
    static class SimDrivetrain implements com.pedropathing.drivetrain.Drivetrain {
        final Robot r; SimDrivetrain(Robot r) { this.r = r; }
        static double[] wheels(com.pedropathing.drivetrain.DrivePowers p) {
            double f = p.forward(), s = p.strafe(), t = p.turn();
            return new double[] {f - s - t, f + s + t, f + s - t, f - s + t};
        }
        public void drive(com.pedropathing.drivetrain.DrivePowers p, boolean manual) { r.power(p.forward(), p.strafe(), false); }
        public double maxScaling(com.pedropathing.drivetrain.DrivePowers cur, com.pedropathing.drivetrain.DrivePowers del) {
            double lambda = 1.0; double[] a = wheels(cur), b = wheels(del);
            for (int i = 0; i < 4; i++) {
                if (Math.abs(b[i]) < 1e-9) continue;
                double t1 = (1.0 - a[i]) / b[i], t2 = (-1.0 - a[i]) / b[i];
                if (t1 >= 0 && t1 < lambda) lambda = t1;
                if (t2 >= 0 && t2 < lambda) lambda = t2;
            }
            return Math.max(0, Math.min(1, lambda));
        }
        public void stop() { stop(true); }
        public void stop(boolean brake) { r.power(0, 0, brake); }
        public Map<String, Object> debug() { return new HashMap<>(); }
        public double interpolateVelocity(double xr, double yr, double th) {
            return 1.0 / (Math.abs(Math.cos(th)) / xr + Math.abs(Math.sin(th)) / yr);
        }
    }

    static class SimLocalizer implements com.pedropathing.localization.Localizer {
        final Robot r; SimLocalizer(Robot r) { this.r = r; }
        public void setPose(com.pedropathing.math.Pose p) { r.x = p.x(); r.y = p.y(); }
        public com.pedropathing.localization.MotionState state() {
            return com.pedropathing.localization.MotionState.ofVelocity(
                new com.pedropathing.math.Pose(r.x, r.y, 0), new com.pedropathing.math.Velocity(r.vx, r.vy, 0));
        }
        public void update() {}
        public void reset() { r.x = r.y = r.vx = r.vy = 0; }
    }

    /** Pedro's ForesightTuner steps (ForwardVelocity, ForwardDeceleration, ForwardBraking, ForwardTranslational), run on the sim. */
    static double[] pedroTune() {
        // Max forward velocity: full power for 72 in, the last 10 readings averaged.
        Robot r = new Robot(); ArrayDeque<Double> last = new ArrayDeque<>();
        while (r.x < 72) { r.power(1, 0, false); r.step(DT); last.add(r.vx); if (last.size() > 10) last.removeFirst(); }
        double vmax = last.stream().mapToDouble(d -> d).average().orElse(0);
        // Natural deceleration: full power to 30 in/s, then float, averaging the deceleration down to 1 in/s.
        r = new Robot(); while (r.vx < 30) { r.power(1, 0, false); r.step(DT); }
        double prev = r.vx, sum = 0; int n = 0;
        while (Math.abs(r.vx) > 1) { r.power(0, 0, false); r.step(DT); sum += (r.vx - prev) / DT; prev = r.vx; n++; }
        double decel = Math.abs(sum / n);
        // Braking: five trials at biased powers 0.7 .. 0.3 over 36 in, braking with 0.001 reverse power.
        List<double[]> vd = new ArrayList<>();
        for (int i = 0; i < 5; i++) {
            double tt = i / 4.0, p = 0.3 + (1 - Math.pow(tt, 1.5)) * 0.4;
            r = new Robot(); while (r.x < 36) { r.power(p, 0, false); r.step(DT); }
            double x0 = r.x, v0 = r.vx, time = 0;
            while (r.vx > 0.25 && time < 7) { r.power(-0.001, 0, false); r.step(DT); time += DT; }
            vd.add(new double[] {v0, r.x - x0});
        }
        double[] brakeFit = com.pedropathing.utils.Utils.quadraticFit(vd);
        // Translational system identification: 0.4 power for 1.2 s.
        r = new Robot(); List<Double> ts = new ArrayList<>(), vs = new ArrayList<>(); double t = 0;
        while (t < 1.2) { r.power(0.4, 0, false); r.step(DT); t += DT; ts.add(t); vs.add(r.vx); }
        int N = ts.size(), start = Math.max(0, N - 15); double A = 0;
        for (int i = start; i < N; i++) A += vs.get(i); A /= (N - start);
        double K = A / 0.4;
        List<Double> xs = new ArrayList<>(), ys = new ArrayList<>();
        for (int i = 0; i < N; i++) {
            double v = vs.get(i) / 0.4;
            if (v > 0.8 * K || v < 0.1 * K) continue;
            ys.add(Math.log(K - v)); xs.add(ts.get(i));
        }
        double[] lr = com.pedropathing.utils.Utils.linearFit(xs.toArray(new Double[0]), ys.toArray(new Double[0]));
        double tau = -1.0 / lr[1];
        double kPl = tau * 10.2 * 10.2 / K, kPs = tau * 6.2 * 6.2 / K, kV = 1 / K;
        return new double[] {vmax, decel, brakeFit[0], brakeFit[1], kPl, kPs, kV, kV * 0.85};
    }

    static double[] PEDRO;

    static com.pedropathing.algorithm.ForesightConfig pedroConfig() {
        double[] c = PEDRO;
        return new com.pedropathing.algorithm.ForesightConfig(cfg -> {
            var pf = com.pedropathing.controllers.Controller.proportional(c[4]);
            var sf = com.pedropathing.controllers.Controller.proportional(c[5]);
            cfg.forwardTranslational.set(com.pedropathing.controllers.Controller.piecewise(sf).put(2.5, pf));
            cfg.strafeTranslational.set(com.pedropathing.controllers.Controller.piecewise(sf).put(2.5, pf));
            cfg.coast.set(com.pedropathing.controllers.Controller.proportionalFeedforward(c[6]));
            cfg.brake.set(com.pedropathing.controllers.Controller.proportionalFeedforward(c[7]));
            cfg.headingFeedback.set(com.pedropathing.controllers.Controller.proportional(1.0));
            cfg.headingBrakeCoefficients.set(com.pedropathing.math.Vector2D.cartesian(0, 0));
            cfg.linearBrakeCoefficients.set(com.pedropathing.math.Matrix.diag(c[2], c[2]));
            cfg.quadraticBrakeCoefficients.set(com.pedropathing.math.Matrix.diag(c[3], c[3]));
            cfg.maxAchievableForwardVelocity.set(c[0]);
            cfg.maxAchievableStrafeVelocity.set(c[0]);
            cfg.naturalForwardDeceleration.set(c[1]);
            cfg.naturalStrafeDeceleration.set(c[1]);
            cfg.maxVelocityConstraint.set(VMAX);
        });
    }

    static Trace runPedro(Scenario sc, double maxT) {
        Trace tr = new Trace(); tr.follower = "Pedro Pathing"; tr.scenario = sc.name;
        double[] cp = sc.cp;
        java.util.function.Supplier<com.pedropathing.paths.Path> mk = () -> {
            if (sc.poly) {
                List<com.pedropathing.paths.Path> segs = new ArrayList<>();
                for (int k = 0; k + 3 < cp.length; k += 2) segs.add(com.pedropathing.api.Paths.line(
                    com.pedropathing.math.Vector2D.cartesian(cp[k], cp[k + 1]), com.pedropathing.math.Vector2D.cartesian(cp[k + 2], cp[k + 3])));
                return com.pedropathing.api.Paths.path(segs.toArray(new com.pedropathing.paths.Path[0])).constant(0);
            }
            return com.pedropathing.api.Paths.path(new com.pedropathing.paths.curves.bezier.BezierCurve(
                com.pedropathing.math.Vector2D.cartesian(cp[0], cp[1]), com.pedropathing.math.Vector2D.cartesian(cp[2], cp[3]),
                com.pedropathing.math.Vector2D.cartesian(cp[4], cp[5]), com.pedropathing.math.Vector2D.cartesian(cp[6], cp[7]))).constant(0);
        };
        for (int i = 0; i < 20; i++) mk.get().getSegments().get(0).curve.length();
        long t0 = System.nanoTime();
        for (int i = 0; i < 20; i++) mk.get().getSegments().get(0).curve.length();
        tr.precomputeMs = (System.nanoTime() - t0) / 1e6 / 20;
        Robot r = new Robot(); r.x = cp[0]; r.y = cp[1]; r.vx = sc.vx0; r.vy = sc.vy0;
        var fol = new com.pedropathing.follower.Follower(new SimLocalizer(r), new SimDrivetrain(r),
            new com.pedropathing.algorithm.Foresight(pedroConfig()));
        fol.follow(mk.get());
        for (double t = 0; t < maxT; t += DT) {
            fol.update(DT);
            r.step(DT);
            tr.rows.add(new double[] {t + DT, r.x, r.y, r.vx, r.vy});
        }
        return tr;
    }

    // ------------------------------------------------------------------ SKIDADDLE
    static double SK_POS = 8, SK_VEL = 0;

    static Trace runSkid(Scenario sc, double maxT) throws Exception {
        Trace tr = new Trace(); tr.follower = "SKIDADDLE"; tr.scenario = sc.name;
        double[] cp = sc.cp;
        Util.Vector[] pts = new Util.Vector[cp.length / 2];
        for (int k = 0; k < pts.length; k++) pts[k] = new Util.Vector(cp[2 * k], cp[2 * k + 1]);
        java.util.function.Supplier<Util.Path.Path> mk = () -> sc.poly ? Pathing.PathGenerator.populate(pts)
            : Pathing.PathGenerator.populate(new Util.Path.Path.Bezier(pts));
        for (int i = 0; i < 20; i++) mk.get();
        long t0 = System.nanoTime(); Util.Path.Path path = null;
        for (int i = 0; i < 20; i++) path = mk.get();
        tr.precomputeMs = (System.nanoTime() - t0) / 1e6 / 20;
        Pathing.Scheduler sch = new Pathing.Scheduler();
        sch.addController(new Pathing.Controllers.LinearController(1, 1, 1, 2));
        Util.MotionState st = new Util.MotionState();
        st.pos = new Util.Twist(pts[0], 0);
        st.vel = new Util.Twist(new Util.Vector(sc.vx0, sc.vy0), 0);
        Pathing.Follower fol = new Pathing.Follower(sch, st, null);
        java.lang.reflect.Field sf = Pathing.Follower.class.getDeclaredField("state"); sf.setAccessible(true);
        Robot r = new Robot(); r.x = cp[0]; r.y = cp[1]; r.vx = sc.vx0; r.vy = sc.vy0;
        for (double t = 0; t < maxT; t += DT) {
            fol.update(new Util.MotionState(), path, DT);
            Util.MotionState plan = (Util.MotionState) sf.get(fol);
            double px = plan.pos.lin.x, py = plan.pos.lin.y, pvx = plan.vel.lin.x, pvy = plan.vel.lin.y;
            double cx = pvx + SK_POS * (px - r.x) + SK_VEL * (pvx - r.vx), cy = pvy + SK_POS * (py - r.y) + SK_VEL * (pvy - r.vy);
            r.power(cx / VFREE + TAU / VFREE * plan.accel.lin.x, cy / VFREE + TAU / VFREE * plan.accel.lin.y, false);
            r.step(DT);
            tr.rows.add(new double[] {t + DT, r.x, r.y, r.vx, r.vy});
        }
        return tr;
    }

    // ------------------------------------------------------------------ main
    static void write(Trace tr, Scenario sc, File dir, PrintWriter summary) throws IOException {
        String f = (tr.scenario + "-" + tr.follower).toLowerCase().replace(' ', '-');
        try (PrintWriter w = new PrintWriter(new File(dir, f + ".csv"))) {
            w.println("t,x,y,vx,vy");
            for (double[] r : tr.rows) w.printf(Locale.US, "%.3f,%.4f,%.4f,%.4f,%.4f%n", r[0], r[1], r[2], r[3], r[4]);
        }
        double[] m = score(tr, sc);
        summary.println(String.format(Locale.US, "%s,%s,%.2f,%.2f,%.2f,%.4f", tr.scenario, tr.follower, m[0], m[1], m[2], tr.precomputeMs));
        System.out.printf(Locale.US, "%-8s %-14s max off path %5.1f in  stopped %5.2f s  %4.1f in from the end  plan %.3f ms  %s%n",
            tr.scenario, tr.follower, m[0], m[1], m[2], tr.precomputeMs, tr.note);
    }

    /** Largest distance from the path; when the robot last moved faster than 2 in/s; and how far from the end it stopped. */
    static double[] score(Trace tr, Scenario sc) {
        double[][] b = sc.samples();
        double dev = 0, stop = 0;
        for (double[] r : tr.rows) {
            double m = Double.MAX_VALUE;
            for (double[] p : b) m = Math.min(m, Math.hypot(r[1] - p[0], r[2] - p[1]));
            dev = Math.max(dev, m);
            if (Math.hypot(r[3], r[4]) >= 2) stop = r[0];
        }
        double[] e = tr.rows.get(tr.rows.size() - 1);
        return new double[] {dev, stop, Math.hypot(e[1] - sc.ex(), e[2] - sc.ey())};
    }

    /** Picks each trajectory follower's tracking gains on the gentle path: least deviation, then quickest settle. */
    static void tune(Scenario sc) throws Exception {
        double[] pos = {1, 2, 3, 4, 6, 8, 12, 16}, vel = {0, 0.25, 0.5, 1, 2, 4};
        double best = Double.MAX_VALUE; double bp = 0, bv = 0;
        for (double p : pos) for (double v : vel) {
            RR_POS = p; RR_VEL = v; double[] m = score(runRR(sc, 9), sc);
            double cost = m[0] + m[1] + 10 * m[2];
            if (cost < best) { best = cost; bp = p; bv = v; }
        }
        RR_POS = bp; RR_VEL = bv;
        System.out.printf(Locale.US, "road runner gains: pos %.2f vel %.2f (cost %.2f)%n", bp, bv, best);
        best = Double.MAX_VALUE;
        for (double p : pos) for (double v : vel) {
            SK_POS = p; SK_VEL = v; double[] m = score(runSkid(sc, 9), sc);
            double cost = m[0] + m[1] + 10 * m[2];
            if (cost < best) { best = cost; bp = p; bv = v; }
        }
        SK_POS = bp; SK_VEL = bv;
        System.out.printf(Locale.US, "skidaddle tracking gains: pos %.2f vel %.2f (cost %.2f)%n", bp, bv, best);
    }

    public static void main(String[] a) throws Exception {
        File dir = new File(a[0]); dir.mkdirs();
        // SKIDADDLE's simulator prints a stack trace whenever its own consistency check trips; keep stderr quiet.
        System.setErr(new PrintStream(OutputStream.nullOutputStream()));
        PEDRO = pedroTune();
        System.out.printf(Locale.US, "pedro tuning: vmax %.2f decel %.2f brake lin %.4f quad %.5f kP %.4f/%.4f kV %.5f brake kV %.5f%n",
            PEDRO[0], PEDRO[1], PEDRO[2], PEDRO[3], PEDRO[4], PEDRO[5], PEDRO[6], PEDRO[7]);
        Scenario gentle = new Scenario("gentle", new double[] {-48, -48, 0, -48, 0, 48, 48, 48}, 0, 0);
        List<Scenario> scs = List.of(
            new Scenario("hairpin", new double[] {-48, -36, 72, -36, 72, 36, -48, 36}, 0, 0),
            new Scenario("corner", new double[] {-60, -40, 10, -40, 60, 10}, 0, 0).polyline(),
            new Scenario("corner90", new double[] {-48, -48, 40, -48, 40, 48}, 0, 0).polyline(),
            gentle,
            new Scenario("moving", new double[] {-48, -48, 0, -48, 0, 48, 48, 48}, 0, 40));
        tune(gentle);
        try (PrintWriter summary = new PrintWriter(new File(dir, "summary.csv"))) {
            summary.println("scenario,follower,max_dev_in,stop_s,end_err_in,plan_ms");
            for (Scenario sc : scs) {
                write(runRR(sc, 9), sc, dir, summary);
                write(runPedro(sc, 9), sc, dir, summary);
                write(runSkid(sc, 9), sc, dir, summary);
            }
        }
        System.exit(0);
    }
}
