sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
systemctl --user force-reload docker-desktop
