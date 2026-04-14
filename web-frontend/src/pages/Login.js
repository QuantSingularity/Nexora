import {
  Lock as LockIcon,
  LocalHospital as HospitalIcon,
  Visibility,
  VisibilityOff,
} from "@mui/icons-material";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    if (!username.trim() || !password.trim()) {
      setError("Please enter both username and password.");
      return;
    }

    setLoading(true);
    // Simulate auth delay
    await new Promise((r) => setTimeout(r, 800));

    // Demo credentials check
    if (
      (username === "admin" && password === "admin") ||
      (username === "demo" && password === "demo123")
    ) {
      localStorage.setItem("auth_token", "demo_token_" + Date.now());
      navigate("/dashboard");
    } else {
      setError("Invalid credentials. Use admin/admin or demo/demo123.");
    }
    setLoading(false);
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background:
          "linear-gradient(135deg, #1565c0 0%, #1976d2 50%, #42a5f5 100%)",
        p: 2,
      }}
    >
      <Card sx={{ maxWidth: 440, width: "100%", borderRadius: 3 }}>
        <CardContent sx={{ p: 5 }}>
          {/* Logo */}
          <Box sx={{ textAlign: "center", mb: 4 }}>
            <Avatar
              sx={{
                bgcolor: "primary.main",
                width: 64,
                height: 64,
                mx: "auto",
                mb: 2,
              }}
            >
              <HospitalIcon sx={{ fontSize: 36 }} />
            </Avatar>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              NEXORA
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Clinical Prediction System
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
            Sign in to your account
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleLogin}>
            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              margin="normal"
              autoComplete="username"
              autoFocus
              disabled={loading}
            />
            <TextField
              fullWidth
              label="Password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              autoComplete="current-password"
              disabled={loading}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading}
              startIcon={<LockIcon />}
              sx={{ mt: 3, mb: 2, py: 1.5, fontWeight: 600 }}
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </Box>

          <Divider sx={{ my: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Demo Credentials
            </Typography>
          </Divider>

          <Box
            sx={{
              bgcolor: "grey.50",
              borderRadius: 2,
              p: 2,
              border: "1px solid",
              borderColor: "grey.200",
            }}
          >
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
            >
              <strong>Admin:</strong> username: <code>admin</code> / password:{" "}
              <code>admin</code>
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
              mt={0.5}
            >
              <strong>Demo:</strong> username: <code>demo</code> / password:{" "}
              <code>demo123</code>
            </Typography>
          </Box>

          <Box sx={{ mt: 3, textAlign: "center" }}>
            <Button
              variant="text"
              size="small"
              onClick={() => navigate("/")}
              sx={{ color: "text.secondary" }}
            >
              ← Back to Home
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Login;
