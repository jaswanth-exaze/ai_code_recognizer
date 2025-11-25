const fileInput = document.getElementById('file-input')
const textInput = document.getElementById('text-input')
const analyzeBtn = document.getElementById('analyze-btn')
const preview = document.getElementById('preview')
const resultEl = document.getElementById('result')
const cameraToggle = document.getElementById('camera-toggle')
const cameraPanel = document.getElementById('camera-panel')
const cameraVideo = document.getElementById('camera-video')
const captureBtn = document.getElementById('capture-btn')
const stopCameraBtn = document.getElementById('stop-camera-btn')

let mediaStream = null

function showPreviewText(txt){
  preview.textContent = txt || 'Drop image or paste text'
}

fileInput.addEventListener('change', (e)=>{
  const f = e.target.files?.[0]
  if(!f) return
  const reader = new FileReader()
  reader.onload = ()=>{
    const img = document.createElement('img')
    img.src = reader.result
    img.style.maxWidth = '100%'
    img.style.maxHeight = '220px'
    preview.innerHTML = ''
    preview.appendChild(img)
  }
  reader.readAsDataURL(f)
})

// toggle or start camera stream
cameraToggle.addEventListener('click', async ()=>{
  if(cameraPanel.classList.contains('active')){
    stopCamera()
    return
  }

  try{
    mediaStream = await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}, audio:false})
    cameraVideo.srcObject = mediaStream
    cameraPanel.classList.add('active')
    cameraPanel.setAttribute('aria-hidden', 'false')
  }catch(err){
    console.error('camera error', err)
    alert('Camera not available or permission denied')
  }
})

function stopCamera(){
  if(mediaStream){
    mediaStream.getTracks().forEach(t=>t.stop())
    mediaStream = null
  }
  cameraVideo.pause()
  cameraVideo.srcObject = null
  cameraPanel.classList.remove('active')
  cameraPanel.setAttribute('aria-hidden', 'true')
}

stopCameraBtn.addEventListener('click', stopCamera)

// capture snapshot from video and show preview (auto-crop performed)
captureBtn.addEventListener('click', async ()=>{
  if(!mediaStream) return
  const video = cameraVideo
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  // perform a simple auto-crop from the captured image
  const cropped = autoCropCanvas(canvas)
  const dataUrl = cropped.toDataURL('image/jpeg', 0.92)
  preview.innerHTML = ''
  const img = document.createElement('img')
  img.src = dataUrl
  img.style.maxWidth = '100%'
  img.style.maxHeight = '220px'
  preview.appendChild(img)
  // stop camera after capture
  stopCamera()
  // put cropped image into a pseudo-file area so it gets sent by analyze
  fileInput.value = ''
  // convert dataURL to blob and set a temporary File object via DataTransfer
  const blob = await (await fetch(dataUrl)).blob()
  const dt = new DataTransfer(); dt.items.add(new File([blob], 'capture.jpg', {type: blob.type}))
  fileInput.files = dt.files
})

async function analyze(){
  const f = fileInput.files?.[0]
  const text = textInput.value.trim()
  const form = new FormData()
  if(f) form.append('file', f)
  if(text) form.append('text', text)

  showPreviewText('Analyzing...')

  try{
    const resp = await fetch('/detect-language', {method:'POST', body: form})
    if(!resp.ok){
      const err = await resp.json().catch(()=>({detail:'server error'}))
      throw new Error(err.detail || 'error')
    }
    const data = await resp.json()
    resultEl.querySelector('.lang').textContent = data.language
    resultEl.querySelector('.confidence').textContent = 'Confidence: ' + (data.confidence||0)
    resultEl.querySelector('.indicators').textContent = (data.indicators||[]).join(' | ')
  }catch(e){
    resultEl.querySelector('.lang').textContent = 'Error'
    resultEl.querySelector('.confidence').textContent = e.message
    resultEl.querySelector('.indicators').textContent = ''
  }
}

// Auto-crop algorithm (basic): find bounding rect of non-white pixels and crop canvas
function autoCropCanvas(canvas){
  const ctx = canvas.getContext('2d')
  const w = canvas.width, h = canvas.height
  const imgd = ctx.getImageData(0,0,w,h)
  const data = imgd.data
  let minX = w, minY = h, maxX = 0, maxY = 0
  const threshold = 240 // near-white considered background
  for(let y=0;y<h;y+=2){
    for(let x=0;x<w;x+=2){
      const idx = (y*w + x)*4
      const r = data[idx], g = data[idx+1], b = data[idx+2]
      if(r < threshold || g < threshold || b < threshold){
        if(x < minX) minX = x
        if(y < minY) minY = y
        if(x > maxX) maxX = x
        if(y > maxY) maxY = y
      }
    }
  }
  // if nothing found, return original
  if(minX === w) return canvas
  // pad a little
  minX = Math.max(0, minX - 10)
  minY = Math.max(0, minY - 10)
  maxX = Math.min(w, maxX + 10)
  maxY = Math.min(h, maxY + 10)
  const cropW = maxX - minX
  const cropH = maxY - minY
  const out = document.createElement('canvas')
  out.width = cropW
  out.height = cropH
  out.getContext('2d').drawImage(canvas, minX, minY, cropW, cropH, 0,0,cropW,cropH)
  return out
}

analyzeBtn.addEventListener('click', analyze)

// Allow text + image drag & drop on preview
preview.addEventListener('dragover', (e)=>{e.preventDefault();preview.style.opacity=0.8})
preview.addEventListener('dragleave', (e)=>{preview.style.opacity=1})
preview.addEventListener('drop', (e)=>{e.preventDefault();preview.style.opacity=1; const f=e.dataTransfer.files?.[0]; if(f){fileInput.files=f; const dt = new DataTransfer(); dt.items.add(f); fileInput.files = dt.files; fileInput.dispatchEvent(new Event('change'))}})
