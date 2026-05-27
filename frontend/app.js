/**
 * Cloud Messaging Service — Frontend
 *
 * API_ENDPOINT is set after SAM deployment.
 * Replace the placeholder below with the value from:
 *   aws cloudformation describe-stacks --stack-name cloud-serverless \
 *     --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text
 */
const API_ENDPOINT =
  window.APP_CONFIG?.apiEndpoint ??
  "https://<your-api-id>.execute-api.<region>.amazonaws.com/prod/send";

/**
 * Collects form data and POSTs it to the API Gateway endpoint.
 * @param {Event} event - The click event from the button
 * @param {"email"|"sms"} typeOfSending - Which channel to use
 */
async function sendMessage(event, typeOfSending) {
  event.preventDefault();

  const button = event.currentTarget;
  const statusEl = document.getElementById("status-message");

  // Reset state
  statusEl.textContent = "";
  statusEl.className = "status";
  button.disabled = true;
  button.textContent = "Sending…";

  const message = document.getElementById("message").value.trim();
  const destinationEmail = document.getElementById("email").value.trim();
  const phoneNumber = document.getElementById("sms").value.trim();

  // Basic client-side validation
  if (!message) {
    showStatus("Please enter a message.", "error");
    resetButton(button, typeOfSending);
    return;
  }
  if (typeOfSending === "email" && !destinationEmail) {
    showStatus("Please enter an email address.", "error");
    resetButton(button, typeOfSending);
    return;
  }
  if (typeOfSending === "sms" && !phoneNumber) {
    showStatus("Please enter a phone number.", "error");
    resetButton(button, typeOfSending);
    return;
  }

  const payload = { typeOfSending, destinationEmail, phoneNumber, message };

  try {
    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await response.json().catch(() => ({}));

    if (response.ok) {
      const channel = typeOfSending === "email" ? "Email" : "SMS";
      showStatus(`✓ ${channel} sent successfully!`, "success");
    } else {
      showStatus(`✗ ${result.error ?? "Unknown error. Please try again."}`, "error");
    }
  } catch {
    showStatus("✗ Network error. Check your connection and try again.", "error");
  } finally {
    resetButton(button, typeOfSending);
  }
}

function showStatus(message, type) {
  const el = document.getElementById("status-message");
  el.textContent = message;
  el.className = `status ${type}`;
}

function resetButton(button, typeOfSending) {
  button.disabled = false;
  button.textContent = typeOfSending === "email" ? "Send Email" : "Send SMS";
}
