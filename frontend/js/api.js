// api.js - Arquivo para gerenciar conexões com a API

const API_BASE_URL = 'http://localhost:5000/api';

/**
 * Obter informações do vídeo a partir da URL
 * @param {string} url - URL do vídeo do YouTube
 * @returns {Promise} Promessa com os dados do vídeo
 */
async function getVideoInfo(url) {
  try {
    const response = await fetch(`${API_BASE_URL}/video-info`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erro ao obter informações do vídeo');
    }

    return await response.json();
  } catch (error) {
    console.error('Erro na requisição de informações do vídeo:', error);
    throw error;
  }
}

/**
 * Iniciar análise completa do vídeo
 * @param {string} url - URL do vídeo do YouTube
 * @returns {Promise} Promessa com o ID do job criado
 */
async function startVideoAnalysis(url) {
  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erro ao iniciar análise do vídeo');
    }

    return await response.json();
  } catch (error) {
    console.error('Erro ao iniciar análise:', error);
    throw error;
  }
}

/**
 * Verificar o status do processamento
 * @param {string} jobId - ID do job de processamento
 * @returns {Promise} Promessa com o status atual
 */
async function checkProcessingStatus(jobId) {
  try {
    const response = await fetch(`${API_BASE_URL}/status/${jobId}`);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erro ao verificar status do processamento');
    }

    return await response.json();
  } catch (error) {
    console.error('Erro ao verificar status:', error);
    throw error;
  }
}

/**
 * Salvar resumo como arquivo markdown
 * @param {string} summary - Conteúdo do resumo em markdown
 * @param {string} videoId - ID do vídeo do YouTube
 * @returns {Promise} Promessa com informações do arquivo salvo
 */
async function saveSummaryAsFile(summary, videoId) {
  try {
    const response = await fetch(`${API_BASE_URL}/save-summary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ summary, video_id: videoId }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erro ao salvar resumo');
    }

    return await response.json();
  } catch (error) {
    console.error('Erro ao salvar resumo:', error);
    throw error;
  }
}

// Exportar as funções para uso no front-end
export { getVideoInfo, startVideoAnalysis, checkProcessingStatus, saveSummaryAsFile };