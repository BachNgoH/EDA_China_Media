import { BASE_URL } from "./const";
import puppeteer from "puppeteer";
import cheerio from "cheerio";
import axios from "axios";
import chrome from "chrome-aws-lambda";

export const scrapeSite = async (endpoint) => {
  try {
    const fetchSite = await axios.get(`${BASE_URL}${endpoint}`);
    const html = await fetchSite.data;
    const status = fetchSite.status;
    const $ = cheerio.load(html);
    return { $, status };
  } catch (e) {
    return Promise.reject(e);
  }
};

export const puppeteerOpenBrowser = async (endpoint, classToWaitFor) => {
  const browser = await puppeteer.launch({
    args: chrome.args,
    executablePath: await chrome.executablePath,
  });

  const page = await browser.newPage();
  
  await page.goto(`${BASE_URL}${endpoint}`, { waitUntil: "load", timeout: 3000 });
  
  // Wait for the specified class to be present
  try {
    await page.waitForSelector(`${classToWaitFor}`, { timeout: 10000 });
  } catch (error) {
    console.error(`Timeout waiting for class "${classToWaitFor}"`);
    await browser.close();
    throw error;
  }

  const content = await page.content();
  console.log("CONTENT: ", content);
  console.log("==========================");
  
  const $ = cheerio.load(content);
  await browser.close();
  return { $ };
};

export function checkEmptyObj(obj) {
  for (var i in obj) return false;
  return true;
}

//
