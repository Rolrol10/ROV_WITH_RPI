// Theme switching
document.addEventListener("DOMContentLoaded", () => {
    const themeSelect = document.getElementById("theme");
    if (themeSelect) {
      themeSelect.value = localStorage.getItem("gui-theme") || "tech";
      themeSelect.addEventListener("change", () => {
        const theme = themeSelect.value;
        document.body.className = `theme-${theme}`;
        localStorage.setItem("gui-theme", theme);
      });
    const savedIP = localStorage.getItem("stream-ip");
    if (savedIP) {
      const ipInput = document.getElementById("streamIP");
      if (ipInput) ipInput.value = savedIP;
    }  
    }
  
    // Slider/number sync
    const syncPairs = [
      "rpiCameraBrightness",
      "rpiCameraContrast",
      "rpiCameraSaturation",
      "rpiCameraSharpness"
    ];
  
    syncPairs.forEach((id) => {
      const slider = document.getElementById(id);
      const number = document.getElementById(id + "Val");
  
      if (slider && number) {
        slider.addEventListener("input", () => number.value = slider.value);
        number.addEventListener("input", () => slider.value = number.value);
        number.value = slider.value;
      }
    });
  
    // Save button
    const form = document.getElementById("settingsForm");
    form?.addEventListener("submit", (e) => {
      e.preventDefault();
  
      const get = (id) => document.getElementById(id)?.value;
      const getNum = (id) => parseFloat(get(id)) || 0;
      const getBool = (id) => document.getElementById(id)?.checked;
  
      const config = {
        resolution: get("resolution"),
        joystick: get("joystick"),
        autoConnect: getBool("autoConnect"),
        theme: get("theme"),
        streamIP: get("streamIP"),
        rpiCameraMode: get("rpiCameraMode"),
        rpiCameraWidth: getNum("rpiCameraWidth"),
        rpiCameraHeight: getNum("rpiCameraHeight"),
        rpiCameraFPS: getNum("rpiCameraFPS"),
        rpiCameraBitrate: getNum("rpiCameraBitrate"),
        rpiCameraIDRPeriod: getNum("rpiCameraIDRPeriod"),
        rpiCameraVFlip: getBool("rpiCameraVFlip"),
        rpiCameraHFlip: getBool("rpiCameraHFlip"),
        rpiCameraBrightness: getNum("rpiCameraBrightness"),
        rpiCameraContrast: getNum("rpiCameraContrast"),
        rpiCameraSaturation: getNum("rpiCameraSaturation"),
        rpiCameraSharpness: getNum("rpiCameraSharpness"),
        rpiCameraExposure: get("rpiCameraExposure"),
        rpiCameraAWB: get("rpiCameraAWB"),
        rpiCameraDenoise: get("rpiCameraDenoise"),
        rpiCameraMetering: get("rpiCameraMetering"),
        rpiCameraShutter: getNum("rpiCameraShutter"),
        rpiCameraGain: getNum("rpiCameraGain"),
        rpiCameraAfMode: get("rpiCameraAfMode")
      };
  
      console.log("🔧 Full settings object:", config);
      localStorage.setItem("stream-ip", config.streamIP);
      alert("Settings saved (not persisted yet)");
      // Optional: send to WebSocket or save to file
    });
  });
  