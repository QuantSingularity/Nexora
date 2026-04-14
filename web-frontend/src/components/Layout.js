import {
  AccountCircle,
  ChevronLeft as ChevronLeftIcon,
  Dashboard as DashboardIcon,
  Home as HomeIcon,
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  People as PeopleIcon,
  Science as ScienceIcon,
  Settings as SettingsIcon,
} from "@mui/icons-material";
import {
  AppBar,
  Avatar,
  Badge,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";

const drawerWidth = 240;

const menuItems = [
  { text: "Dashboard", icon: <DashboardIcon />, path: "/dashboard" },
  { text: "Patients", icon: <PeopleIcon />, path: "/patients" },
  { text: "Models", icon: <ScienceIcon />, path: "/models" },
  { text: "Settings", icon: <SettingsIcon />, path: "/settings" },
];

function Layout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(!isMobile);
  const [anchorEl, setAnchorEl] = useState(null);

  const handleDrawerToggle = () => setOpen((prev) => !prev);
  const handleProfileMenuOpen = (event) => setAnchorEl(event.currentTarget);
  const handleProfileMenuClose = () => setAnchorEl(null);

  const handleLogout = () => {
    handleProfileMenuClose();
    localStorage.removeItem("auth_token");
    navigate("/");
  };

  // Active check: supports nested routes like /patients/:id
  const isActive = (path) => {
    if (path === "/dashboard") return location.pathname === "/dashboard";
    return location.pathname.startsWith(path);
  };

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar
        position="fixed"
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
          background: "white",
          color: "primary.main",
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="toggle drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            {open && !isMobile ? <ChevronLeftIcon /> : <MenuIcon />}
          </IconButton>

          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Typography
              variant="h6"
              noWrap
              component={Link}
              to="/"
              sx={{ fontWeight: 800, textDecoration: "none", color: "inherit" }}
            >
              NEXORA
            </Typography>
            <Typography
              variant="caption"
              sx={{
                ml: 1,
                opacity: 0.55,
                display: { xs: "none", sm: "block" },
              }}
            >
              Clinical Prediction System
            </Typography>
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <Tooltip title="Home">
              <IconButton color="inherit" component={Link} to="/">
                <HomeIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Notifications">
              <IconButton color="inherit">
                <Badge badgeContent={3} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>
            <Tooltip title="Account">
              <IconButton
                edge="end"
                aria-label="account"
                aria-haspopup="true"
                onClick={handleProfileMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: "primary.main" }}>
                  <AccountCircle />
                </Avatar>
              </IconButton>
            </Tooltip>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleProfileMenuClose}
              transformOrigin={{ horizontal: "right", vertical: "top" }}
              anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
              PaperProps={{ elevation: 3, sx: { minWidth: 160, mt: 0.5 } }}
            >
              <MenuItem disabled>
                <Typography variant="caption" color="text.secondary">
                  Signed in as Admin
                </Typography>
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleProfileMenuClose}>Profile</MenuItem>
              <MenuItem onClick={handleProfileMenuClose}>My Account</MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout} sx={{ color: "error.main" }}>
                Logout
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant={isMobile ? "temporary" : "persistent"}
        open={open}
        onClose={isMobile ? handleDrawerToggle : undefined}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
            background: theme.palette.background.default,
            borderRight: "1px solid rgba(0,0,0,0.08)",
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: "auto", mt: 1 }}>
          <List>
            {menuItems.map((item) => {
              const active = isActive(item.path);
              return (
                <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
                  <ListItemButton
                    component={Link}
                    to={item.path}
                    selected={active}
                    sx={{
                      borderRadius: "0 24px 24px 0",
                      mx: 1,
                      backgroundColor: active
                        ? "rgba(25, 118, 210, 0.12)"
                        : "transparent",
                      "&:hover": {
                        backgroundColor: active
                          ? "rgba(25, 118, 210, 0.18)"
                          : "rgba(25, 118, 210, 0.06)",
                      },
                      "&.Mui-selected": {
                        backgroundColor: "rgba(25, 118, 210, 0.12)",
                      },
                      "&.Mui-selected:hover": {
                        backgroundColor: "rgba(25, 118, 210, 0.18)",
                      },
                    }}
                    onClick={isMobile ? handleDrawerToggle : undefined}
                  >
                    <ListItemIcon
                      sx={{
                        color: active ? "primary.main" : "text.secondary",
                        minWidth: 40,
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.text}
                      primaryTypographyProps={{
                        fontWeight: active ? 700 : 400,
                        color: active ? "primary.main" : "text.primary",
                        fontSize: "0.9rem",
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ px: 2 }}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mb: 1, display: "block" }}
            >
              System Status
            </Typography>
            <Box
              sx={{
                p: 1.5,
                bgcolor: "success.light",
                color: "success.contrastText",
                borderRadius: 2,
                fontSize: "0.8rem",
                display: "flex",
                alignItems: "center",
                gap: 1,
              }}
            >
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  bgcolor: "white",
                  flexShrink: 0,
                  "@keyframes pulse": {
                    "0%": { boxShadow: "0 0 0 0 rgba(255,255,255,0.6)" },
                    "70%": { boxShadow: "0 0 0 6px rgba(255,255,255,0)" },
                    "100%": { boxShadow: "0 0 0 0 rgba(255,255,255,0)" },
                  },
                  animation: "pulse 2s infinite",
                }}
              />
              All systems operational
            </Box>
          </Box>

          <Box sx={{ px: 2, mt: 3 }}>
            <Typography variant="caption" color="text.disabled">
              Nexora v1.2.0
            </Typography>
          </Box>
        </Box>
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          pt: 10,
          minHeight: "100vh",
          bgcolor: "background.default",
          width: "100%",
          transition: theme.transitions.create(["margin", "width"], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          ...(open &&
            !isMobile && {
              marginLeft: 0,
              width: `calc(100% - ${drawerWidth}px)`,
              transition: theme.transitions.create(["margin", "width"], {
                easing: theme.transitions.easing.easeOut,
                duration: theme.transitions.duration.enteringScreen,
              }),
            }),
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}

export default Layout;
