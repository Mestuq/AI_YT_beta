// JavaScript code to replace "(uploader)" and "(tag)" with appropriate <span> elements

document.addEventListener("DOMContentLoaded", function () 
{
    const elements = document.getElementsByTagName("*");
    for (const element of elements) 
    {
      if (element.hasChildNodes()) 
      {
        replaceText(element);
      }
    }
  });
  
  function replaceText(element) 
  {
    if (element.nodeType === Node.TEXT_NODE) 
    {
      const text = element.textContent;
      const reUploader = /\(uploader\)/gi;
      const reTag = /\(tag\)/gi;
  
      if (reUploader.test(text)) 
      {
        const replacedText = text.replace(reUploader, '<span class="badge text-bg-danger">Uploader</span> ');
        const tempElement = document.createElement("div");
        tempElement.innerHTML = replacedText;
        while (tempElement.firstChild) {
          element.parentNode.insertBefore(tempElement.firstChild, element);
        }
        element.parentNode.removeChild(element);
      } 
      else if (reTag.test(text)) 
      {
        const replacedText = text.replace(reTag, '<span class="badge text-bg-success">Tag</span> ');
        const tempElement = document.createElement("div");
        tempElement.innerHTML = replacedText;
        while (tempElement.firstChild) {
          element.parentNode.insertBefore(tempElement.firstChild, element);
        }
        element.parentNode.removeChild(element);
      }
    } else 
    {
      for (const childElement of element.childNodes) 
      {
        replaceText(childElement);
      }
    }
  }
  