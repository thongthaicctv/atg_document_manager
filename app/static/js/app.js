document.addEventListener("submit", function (event) {
  const form = event.target;
  const message = form.getAttribute("data-confirm");
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});

function formatFileSize(bytes) {
  if (!Number.isFinite(bytes)) {
    return "";
  }
  if (bytes < 1024) {
    return bytes + " B";
  }
  if (bytes < 1024 * 1024) {
    return (bytes / 1024).toFixed(1) + " KB";
  }
  return (bytes / 1024 / 1024).toFixed(1) + " MB";
}

function createStoredFileInput(container, files) {
  const holder = container.querySelector("[data-capture-holder]");
  if (!holder || !files.length) {
    return null;
  }

  const input = document.createElement("input");
  input.type = "file";
  input.name = container.getAttribute("data-capture-field-name") || "files";
  input.multiple = true;
  input.className = "visually-hidden";

  const transfer = new DataTransfer();
  files.forEach(function (file) {
    transfer.items.add(file);
  });
  input.files = transfer.files;
  holder.appendChild(input);
  return input;
}

function captureEntries(container) {
  const holder = container.querySelector("[data-capture-holder]");
  if (!holder) {
    return [];
  }

  return Array.from(holder.querySelectorAll("input[type='file']")).flatMap(function (input) {
    return Array.from(input.files || []).map(function (file, fileIndex) {
      return { input: input, file: file, fileIndex: fileIndex };
    });
  });
}

function capturedFiles(container) {
  return captureEntries(container).map(function (entry) {
    return entry.file;
  });
}

function removeCapturedEntry(container, entry) {
  const transfer = new DataTransfer();
  Array.from(entry.input.files || []).forEach(function (file, index) {
    if (index !== entry.fileIndex) {
      transfer.items.add(file);
    }
  });

  if (transfer.files.length) {
    entry.input.files = transfer.files;
  } else {
    entry.input.remove();
  }
  renderCaptureList(container);
}

function renderCaptureList(container) {
  const count = container.querySelector("[data-capture-count]");
  const list = container.querySelector("[data-capture-list]");
  const clearButton = container.querySelector("[data-capture-clear]");
  const unit = container.getAttribute("data-capture-unit") || "ảnh";
  const emptyText = container.getAttribute("data-capture-empty") || "Chưa có ảnh nào";
  const entries = captureEntries(container);

  if (container._capturePreviewUrls) {
    container._capturePreviewUrls.forEach(URL.revokeObjectURL);
  }
  container._capturePreviewUrls = [];

  if (count) {
    count.textContent = entries.length ? entries.length + " " + unit + " đã chọn" : emptyText;
  }
  if (clearButton) {
    clearButton.disabled = entries.length === 0;
  }
  if (!list) {
    return;
  }

  list.replaceChildren();
  entries.forEach(function (entry, index) {
    const item = document.createElement("div");
    item.className = "captured-file-item";

    const meta = document.createElement("div");
    meta.className = "captured-file-meta";

    if (entry.file.type.startsWith("image/")) {
      const thumbUrl = URL.createObjectURL(entry.file);
      container._capturePreviewUrls.push(thumbUrl);
      const thumb = document.createElement("img");
      thumb.className = "captured-file-thumb";
      thumb.src = thumbUrl;
      thumb.alt = "Trang " + (index + 1);
      meta.appendChild(thumb);
    }

    const text = document.createElement("div");
    text.className = "captured-file-text";

    const name = document.createElement("span");
    name.className = "captured-file-name";
    name.textContent = index + 1 + ". " + entry.file.name;

    const size = document.createElement("span");
    size.className = "captured-file-size";
    size.textContent = formatFileSize(entry.file.size);

    text.append(name, size);
    meta.appendChild(text);

    const removeButton = document.createElement("button");
    removeButton.className = "btn btn-sm btn-outline-danger";
    removeButton.type = "button";
    removeButton.title = "Xóa trang này";
    removeButton.innerHTML = '<i class="bi bi-trash"></i>';
    removeButton.addEventListener("click", function () {
      removeCapturedEntry(container, entry);
    });

    item.append(meta, removeButton);
    list.append(item);
  });
}

function addCapturedFiles(container, files) {
  const usableFiles = files.filter(function (file) {
    return file && file.size > 0;
  });
  if (!usableFiles.length) {
    return;
  }

  createStoredFileInput(container, usableFiles);
  renderCaptureList(container);
}

function createCaptureInput() {
  const input = document.createElement("input");
  input.className = "form-control capture-camera-input";
  input.type = "file";
  input.accept = "image/*";
  input.setAttribute("capture", "environment");
  input.multiple = true;
  input.setAttribute("data-capture-input", "");
  return input;
}

function wireCaptureInput(container, picker) {
  picker.addEventListener("change", function () {
    const selectedFiles = Array.from(picker.files || []);
    addCapturedFiles(container, selectedFiles);
    picker.value = "";
  });
}

let activeCameraContainer = null;
let activeCameraStream = null;
let cameraModal = null;
let cameraVideo = null;
let cameraSelect = null;

function stopCameraStream() {
  if (activeCameraStream) {
    activeCameraStream.getTracks().forEach(function (track) {
      track.stop();
    });
  }
  activeCameraStream = null;
  if (cameraVideo) {
    cameraVideo.srcObject = null;
  }
}

function ensureCameraModal() {
  if (cameraModal) {
    return cameraModal;
  }

  const wrapper = document.createElement("div");
  wrapper.className = "modal fade";
  wrapper.id = "scanCameraModal";
  wrapper.tabIndex = -1;
  wrapper.setAttribute("aria-hidden", "true");
  wrapper.innerHTML = [
    '<div class="modal-dialog modal-xl modal-dialog-centered">',
    '  <div class="modal-content scan-modal-content">',
    '    <div class="modal-header">',
    '      <h2 class="modal-title h5"><i class="bi bi-camera-video"></i> Scan văn bản</h2>',
    '      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Đóng"></button>',
    "    </div>",
    '    <div class="modal-body">',
    '      <div class="scan-video-frame">',
    '        <video class="scan-video" autoplay playsinline muted></video>',
    '        <div class="scan-page-guide"></div>',
    "      </div>",
    '      <div class="row g-2 align-items-end mt-3">',
    '        <div class="col-12 col-md">',
    '          <label class="form-label" for="scanCameraSelect">Camera</label>',
    '          <select class="form-select" id="scanCameraSelect"></select>',
    "        </div>",
    '        <div class="col-12 col-md-auto">',
    '          <button class="btn btn-primary w-100" type="button" data-scan-shot><i class="bi bi-camera"></i> Chụp trang</button>',
    "        </div>",
    '        <div class="col-12 col-md-auto">',
    '          <button class="btn btn-outline-secondary w-100" type="button" data-bs-dismiss="modal">Xong</button>',
    "        </div>",
    "      </div>",
    '      <div class="small text-muted mt-2" data-scan-message></div>',
    "    </div>",
    "  </div>",
    "</div>",
  ].join("");
  document.body.appendChild(wrapper);

  cameraVideo = wrapper.querySelector(".scan-video");
  cameraSelect = wrapper.querySelector("#scanCameraSelect");
  const shotButton = wrapper.querySelector("[data-scan-shot]");
  const message = wrapper.querySelector("[data-scan-message]");

  cameraSelect.addEventListener("change", function () {
    startCamera(cameraSelect.value);
  });

  shotButton.addEventListener("click", function () {
    if (!activeCameraContainer || !cameraVideo || !cameraVideo.videoWidth) {
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = cameraVideo.videoWidth;
    canvas.height = cameraVideo.videoHeight;
    const context = canvas.getContext("2d", { alpha: false });
    context.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      function (blob) {
        if (!blob) {
          return;
        }
        const file = new File([blob], "scan_page_" + Date.now() + ".jpg", { type: "image/jpeg" });
        addCapturedFiles(activeCameraContainer, [file]);
        if (message) {
          const total = capturedFiles(activeCameraContainer).length;
          message.textContent = "Đã chụp " + total + " trang.";
        }
      },
      "image/jpeg",
      0.94
    );
  });

  wrapper.addEventListener("hidden.bs.modal", function () {
    stopCameraStream();
    activeCameraContainer = null;
  });

  cameraModal = new bootstrap.Modal(wrapper);
  return cameraModal;
}

async function populateCameraSelect(activeDeviceId) {
  if (!cameraSelect || !navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
    return;
  }
  const devices = await navigator.mediaDevices.enumerateDevices();
  const videoDevices = devices.filter(function (device) {
    return device.kind === "videoinput";
  });
  cameraSelect.replaceChildren();
  videoDevices.forEach(function (device, index) {
    const option = document.createElement("option");
    option.value = device.deviceId;
    option.textContent = device.label || "Camera " + (index + 1);
    if (activeDeviceId && activeDeviceId === device.deviceId) {
      option.selected = true;
    }
    cameraSelect.appendChild(option);
  });
  cameraSelect.disabled = videoDevices.length <= 1;
}

async function startCamera(deviceId) {
  stopCameraStream();
  const message = document.querySelector("[data-scan-message]");
  if (!canUseDirectCamera()) {
    if (message) {
      message.textContent = "Chrome chỉ cho mở camera trực tiếp khi dùng HTTPS hoặc localhost.";
    }
    return;
  }

  const video = deviceId
    ? { deviceId: { exact: deviceId }, width: { ideal: 1920 }, height: { ideal: 1080 } }
    : { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } };

  try {
    activeCameraStream = await navigator.mediaDevices.getUserMedia({ video: video, audio: false });
    cameraVideo.srcObject = activeCameraStream;
    await cameraVideo.play();
    const track = activeCameraStream.getVideoTracks()[0];
    await populateCameraSelect(track && track.getSettings ? track.getSettings().deviceId : deviceId);
    if (message) {
      message.textContent = "";
    }
  } catch (error) {
    if (message) {
      message.textContent = "Không mở được camera. Nếu đang truy cập qua IP/tên miền, trình duyệt có thể yêu cầu HTTPS.";
    }
  }
}

function canUseDirectCamera() {
  return Boolean(
    window.isSecureContext &&
      navigator.mediaDevices &&
      typeof navigator.mediaDevices.getUserMedia === "function"
  );
}

function openNativeCameraPicker(container) {
  const picker = container.querySelector("[data-capture-input]");
  if (!picker) {
    return;
  }
  picker.click();
}

function openCameraModal(container) {
  if (!canUseDirectCamera()) {
    openNativeCameraPicker(container);
    return;
  }
  activeCameraContainer = container;
  ensureCameraModal().show();
  startCamera();
}

function initMultiCapture(container) {
  const picker = container.querySelector("[data-capture-input]");
  const holder = container.querySelector("[data-capture-holder]");
  const clearButton = container.querySelector("[data-capture-clear]");
  const cameraButton = container.querySelector("[data-capture-webcam]");
  if (!picker || !holder) {
    return;
  }

  wireCaptureInput(container, picker);

  if (clearButton) {
    clearButton.addEventListener("click", function () {
      holder.replaceChildren();
      renderCaptureList(container);
    });
  }

  if (cameraButton) {
    cameraButton.addEventListener("click", function () {
      openCameraModal(container);
    });
    if (!canUseDirectCamera()) {
      cameraButton.innerHTML = '<i class="bi bi-camera"></i> Chụp/chọn trang';
      cameraButton.title = "Chrome Android trên HTTP LAN sẽ dùng camera hệ thống của điện thoại.";
    }
  }

  renderCaptureList(container);
}

document.querySelectorAll("[data-multi-capture]").forEach(initMultiCapture);
