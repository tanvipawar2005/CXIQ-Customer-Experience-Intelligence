import axios from 'axios'

// =========================================================
// AXIOS INSTANCE
// =========================================================

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})


// =========================================================
// CLERK AUTHENTICATION
// =========================================================

// Attach the signed-in user's Clerk session token, when available.
//
// This means every request made through `api` automatically sends:
//
// Authorization: Bearer <token>
//
// Guests can still use endpoints that support guest access.
api.interceptors.request.use(async (config) => {
  try {
    const clerk =
      typeof window !== 'undefined'
        ? window.Clerk
        : null

    if (clerk?.session) {
      const token = await clerk.session.getToken()

      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
  } catch {
    // Clerk may not be loaded/configured.
    // Continue as a guest request.
  }

  return config
})


// =========================================================
// ERROR HANDLING
// =========================================================

function extractErrorMessage(error) {
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail

    if (typeof detail === 'string') {
      return detail
    }

    if (Array.isArray(detail)) {
      return detail
        .map((d) => d.msg)
        .join(' ')
    }
  }

  if (error.code === 'ECONNABORTED') {
    return 'The request took too long. Please try again.'
  }

  if (!error.response) {
    return 'Could not reach the CXIQ backend. Make sure the API server is running.'
  }

  return 'Something went wrong. Please try again.'
}


// =========================================================
// HEALTH CHECK
// =========================================================

export async function checkHealth() {
  const res = await api.get('/health')
  return res.data
}


// =========================================================
// SINGLE FEEDBACK ANALYSIS
// =========================================================

export async function analyzeFeedback({
  text,
  domain,
  rating,
}) {
  try {
    const res = await api.post(
      '/analyze',
      {
        text,
        domain,
        rating,
      }
    )

    return res.data
  } catch (err) {
    throw new Error(
      extractErrorMessage(err)
    )
  }
}


// =========================================================
// DATASET UPLOAD / BATCH ANALYSIS
// =========================================================

export async function uploadDataset({
  file,
  domain,
}) {
  try {
    const formData = new FormData()

    formData.append(
      'file',
      file
    )

    formData.append(
      'domain',
      domain || 'other'
    )

    const res = await api.post(
      '/analyze/batch',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },

        // Batch analysis can take longer because multilingual
        // reviews may require translation.
        timeout: 120000,
      }
    )

    return res.data
  } catch (err) {
    throw new Error(
      extractErrorMessage(err)
    )
  }
}


// =========================================================
// DATASET PREVIEW
// =========================================================

export async function getDatasetPreview(
  datasetId,
  rows = 10
) {
  try {
    const res = await api.get(
      `/analyze/batch/${datasetId}/preview`,
      {
        params: {
          rows,
        },
      }
    )

    return res.data
  } catch (err) {
    throw new Error(
      extractErrorMessage(err)
    )
  }
}


// =========================================================
// DASHBOARD
// =========================================================

export async function getDashboard(
  datasetId,
  language
) {
  try {
    const params = {
      dataset_id: datasetId,
    }

    if (
      language &&
      language !== 'All'
    ) {
      params.language = language
    }

    const res = await api.get(
      '/dashboard',
      {
        params,
      }
    )

    return res.data
  } catch (err) {
    throw new Error(
      extractErrorMessage(err)
    )
  }
}


// =========================================================
// RETRY FAILED TRANSLATIONS
// =========================================================

export async function retryFailedTranslations(
  datasetId
) {
  try {
    const res = await api.post(
      `/analyze/batch/${datasetId}/retry-failed`
    )

    return res.data
  } catch (err) {
    throw new Error(
      extractErrorMessage(err)
    )
  }
}


// =========================================================
// LANGUAGE COMPARISON
// =========================================================

export async function compareLanguages({
  entries,
  domain,
}) {
  try {
    const res = await api.post(
      '/analyze/compare',
      {
        entries,
        domain,
      }
    )

    return res.data
  } catch (err) {
    throw new Error(
      extractErrorMessage(err)
    )
  }
}


// =========================================================
// ASK CXIQ
// =========================================================

export async function askCxiq({
  datasetId,
  question,
}) {
  try {
    const res = await api.post(
      '/dashboard/ask',
      {
        dataset_id: datasetId,
        question,
      }
    )

    return res.data
  } catch (err) {
    throw new Error(
      extractErrorMessage(err)
    )
  }
}

// =========================================================
// DOWNLOAD URL - BACKWARD COMPATIBILITY
// =========================================================

export function getDownloadUrl(datasetId) {
  return `/api/analyze/batch/${datasetId}/download`
}

// =========================================================
// DOWNLOAD ANALYZED RESULTS CSV
// =========================================================

export async function downloadResults(
  datasetId
) {
  try {

    /*
     * IMPORTANT:
     *
     * Previously the dashboard used:
     *
     * <a href="/api/analyze/batch/.../download">
     *
     * That caused the browser to make the request directly.
     * Therefore our Axios interceptor was NOT executed and
     * the Clerk Authorization token was not attached.
     *
     * Private datasets were consequently returned as 404.
     *
     * Using `api.get()` here means the normal Axios
     * authentication interceptor runs automatically.
     */

    const res = await api.get(
      `/analyze/batch/${datasetId}/download`,
      {
        responseType: 'blob',

        // Keep normal API timeout for CSV generation.
        timeout: 30000,
      }
    )


    // -----------------------------------------------------
    // Create browser Blob URL
    // -----------------------------------------------------

    const blobUrl =
      window.URL.createObjectURL(
        res.data
      )


    // -----------------------------------------------------
    // Determine filename
    // -----------------------------------------------------

    let filename =
      `cxiq_results_${datasetId.slice(0, 8)}.csv`


    /*
     * If the backend supplied:
     *
     * Content-Disposition:
     * attachment; filename=cxiq_results_xxxxxxxx.csv
     *
     * use that filename.
     */

    const contentDisposition =
      res.headers?.['content-disposition']

    if (contentDisposition) {
      const match =
        contentDisposition.match(
          /filename="?([^"]+)"?/i
        )

      if (
        match &&
        match[1]
      ) {
        filename =
          match[1].trim()
      }
    }


    // -----------------------------------------------------
    // Trigger browser download
    // -----------------------------------------------------

    const link =
      document.createElement('a')

    link.href = blobUrl
    link.download = filename

    document.body.appendChild(
      link
    )

    link.click()

    link.remove()


    // -----------------------------------------------------
    // Clean up temporary Blob URL
    // -----------------------------------------------------

    window.URL.revokeObjectURL(
      blobUrl
    )

    return true

  } catch (err) {

    /*
     * Because responseType is "blob", backend JSON errors
     * may arrive as a Blob rather than a normal JSON object.
     * Try to extract the backend error message when possible.
     */

    if (
      err.response?.data instanceof Blob
    ) {
      try {
        const text =
          await err.response.data.text()

        const parsed =
          JSON.parse(text)

        if (parsed?.detail) {
          throw new Error(
            parsed.detail
          )
        }

      } catch (blobError) {

        // If we deliberately created an Error above,
        // preserve that message.
        if (
          blobError instanceof Error &&
          blobError.message &&
          blobError.message !==
            'Unexpected end of JSON input'
        ) {
          throw blobError
        }
      }
    }

    throw new Error(
      extractErrorMessage(err)
    )
  }
}


// =========================================================
// USER DATASETS
// =========================================================

export async function getMyDatasets() {
  try {
    const res =
      await api.get(
        '/datasets/my'
      )

    return res.data.datasets

  } catch (err) {
    throw new Error(
      extractErrorMessage(err)
    )
  }
}


// =========================================================
// DATASET DETAILS
// =========================================================

export async function getDatasetDetail(
  datasetId
) {
  try {
    const res =
      await api.get(
        `/datasets/${datasetId}`
      )

    return res.data

  } catch (err) {
    throw new Error(
      extractErrorMessage(err)
    )
  }
}


// =========================================================
// SAMPLE DATASET
// =========================================================

export async function loadSampleDataset() {
  try {
    const res =
      await api.post(
        '/datasets/sample'
      )

    return res.data

  } catch (err) {
    throw new Error(
      extractErrorMessage(err)
    )
  }
}


// =========================================================
// DEFAULT AXIOS EXPORT
// =========================================================

export default api