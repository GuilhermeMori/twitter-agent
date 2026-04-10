const fs = require('fs');
const path = require('path');

/**
 * Retorna o caminho da pasta da última execução
 */
function getLatestRunPath() {
  const historyDir = path.join(__dirname, '../../output/history');

  if (!fs.existsSync(historyDir)) {
    return null;
  }

  const folders = fs.readdirSync(historyDir)
    .filter(f => fs.statSync(path.join(historyDir, f)).isDirectory())
    .sort()
    .reverse(); // Mais recente primeiro

  if (folders.length === 0) {
    return null;
  }

  return path.join(historyDir, folders[0]);
}

/**
 * Retorna o caminho de um arquivo na última execução
 */
function getLatestFile(filename) {
  const latestRun = getLatestRunPath();
  if (!latestRun) {
    return null;
  }
  return path.join(latestRun, filename);
}

module.exports = {
  getLatestRunPath,
  getLatestFile
};
