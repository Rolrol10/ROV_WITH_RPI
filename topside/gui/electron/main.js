// electron/main.js
const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 720,
    frame: true,           // ❌ no window bar
    fullscreenable: true,
    resizable: true,
    webPreferences: {
      nodeIntegration: false
    }
  });

  // Load the GUI HTML file
  win.loadFile(path.join(__dirname, '../index.html'));
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
