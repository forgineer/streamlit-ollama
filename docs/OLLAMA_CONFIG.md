Changing the Ollama Host
The best and safest way to change the Ollama host is to set an environment variable. Environment variables are a standard way to configure applications and are less likely to be overwritten or cause issues during system updates than modifying system files directly.

There are a few ways to set this variable:

Option 1: Temporary (for testing)
You can set the variable directly in your terminal before starting the Ollama service. This is useful for testing purposes.

Bash

OLLAMA_HOST=0.0.0.0 ollama serve
Option 2: Permanent (recommended)
For a permanent solution, create or edit the ollama.service override file. This is the correct way to modify systemd service settings without directly altering the original file. This approach ensures your changes persist through updates.

Create the directory for the override file:

Bash

sudo mkdir -p /etc/systemd/system/ollama.service.d/
Create and open the override file in a text editor like nano:

Bash

sudo nano /etc/systemd/system/ollama.service.d/override.conf
Add the following content to the file:

Ini, TOML

[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Save and close the file. In nano, press Ctrl+X, then Y, then Enter.

Reload the systemd daemon to apply the changes:

Bash

sudo systemctl daemon-reload
Restart the Ollama service:

Bash

sudo systemctl restart ollama
After completing these steps, your Ollama server will be accessible on your local network at http://<your_server_ip>:11434.

Why not edit the original file?
Directly editing the /lib/systemd/system/ollama.service file is a bad practice. System package managers may overwrite this file during updates, causing your changes to be lost. Using a systemd override file is the standard and recommended method for making custom changes to a service's configuration.