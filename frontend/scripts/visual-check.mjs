import { chromium } from "playwright-core";
import path from "node:path";

const executablePath = process.env.CHROME_PATH ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const browser = await chromium.launch({ executablePath, headless: true });

async function verifyViewport(name, viewport) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
  await page.locator("button.primary-button").click();
  await page.locator(".workspace").waitFor();

  const dimensions = await page.evaluate(() => ({
    viewport: window.innerWidth,
    content: document.documentElement.scrollWidth,
  }));
  if (dimensions.content > dimensions.viewport) {
    throw new Error(`${name} has horizontal overflow: ${dimensions.content}px > ${dimensions.viewport}px`);
  }

  const target = path.resolve("..", "qa", `workspace-${name}.png`);
  await page.screenshot({ path: target, fullPage: true });
  await context.close();
  return dimensions;
}

try {
  const desktop = await verifyViewport("desktop", { width: 1440, height: 900 });
  const mobile = await verifyViewport("mobile", { width: 390, height: 844 });
  console.log(JSON.stringify({ desktop, mobile }));
} finally {
  await browser.close();
}
