const jwt = require("jsonwebtoken");

const JWT_SECRET = process.env.JWT_SECRET || "super_secret_production_rag_key_change_in_prod_12345";

/**
 * Issue a guest or session token if not already authenticated
 */
function issueToken(userId = "guest_user", role = "user") {
  return jwt.sign({ userId, role }, JWT_SECRET, { expiresIn: "7d" });
}

/**
 * Middleware to verify incoming JWT in Authorization header
 * Auto-creates guest session if none provided so users can use the app immediately
 */
function verifyToken(req, res, next) {
  const authHeader = req.headers["authorization"];
  const token = authHeader && authHeader.split(" ")[1];

  if (!token) {
    // Issue transparent guest session
    req.user = { userId: `guest_${Date.now()}`, role: "guest" };
    req.isGuest = true;
    return next();
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      // If token expired or invalid, fall back to guest session
      req.user = { userId: `guest_${Date.now()}`, role: "guest" };
      req.isGuest = true;
      return next();
    }
    req.user = user;
    req.isGuest = false;
    next();
  });
}

module.exports = {
  issueToken,
  verifyToken,
  JWT_SECRET,
};
