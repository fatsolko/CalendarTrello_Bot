first_page = """
<head>
  <meta http-equiv="refresh" content="5; URL={url1}" />
</head>
<body>
  <p>If you are not redirected in five seconds, <a href="{url2}">click here</a>.</p>
</body>
"""
error_page = """
<!DOCTYPE html>
<html>
<body>
<meta charset="utf-8">
<h1>Прывiтанне!</h1>
<img src="https://files.liveworksheets.com/def_files/2020/4/1/4011430193088/4011430193088001.jpg?ssl=1" width="450" height="600"/>
</body>
</html>

"""
redirect_web_page_code = """
<!DOCTYPE html>
<html lang="en">
  <head>
  <meta content="text/html;charset=utf-8" http-equiv="Content-Type">
<meta content="utf-8" http-equiv="encoding">
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Redirect</title>
  </head>
  <body>
    <style>
      body {
        margin: 20% auto;
        font-family: monospace;
        background: url("https://i.gifer.com/NvL.gif");
        text-transform: lowercase;
      }

      .text-center {
        display: flex;
        align-items: center;
        justify-content: center;
      }

      p {
        display: inline-block;
        background: black;
        text-shadow: 1px 1px 15px #17ff00;
        text-align: center;
        font-size: 26px;
        color: #17ff00;
      }

      .input-container {
        margin: 0 auto;
        display: flex;
        width: 80%;
        margin-bottom: 2em;
      }

      input {
        width: 100%;
        font-family: monospace;
        margin-right: 12px;
        box-shadow: inset -1px -1px #fff, inset 1px 1px grey, inset -2px -2px #dfdfdf,
          inset 2px 2px #0a0a0a;
        box-sizing: border-box;
        padding: 3px 4px;
      }

      input:focus {
        outline: none;
      }

      button {
        background: silver;
        box-shadow: inset -1px -1px #0a0a0a, inset 1px 1px #fff, inset -2px -2px grey,
          inset 2px 2px #dfdfdf;
        border: none;
        border-radius: 0;
        box-sizing: border-box;
        min-height: 23px;
        min-width: 75px;
        padding: 0 12px;
      }

      button:active {
        box-shadow: inset -1px -1px #fff, inset 1px 1px #0a0a0a, inset -2px -2px #dfdfdf,
          inset 2px 2px grey;
        padding: 2px 11px 0 13px;
      }

      svg {
        vertical-align: text-bottom;
        fill: #30363d;
      }
    </style>

    <div class="text-center">
      <p>Вы вошли в аккаунт, отправьте это сообщение боту:</p>
    </div>

    <div class="input-container">
      <input
        type="text"
        value="/token token:{access_token}, refresh:{refresh_token}(end)"
        readonly
        onclick="this.select()"
      />
      <button class="copy">Copy</button>
    </div>

    <div class="text-center">
      <button class="copy">
        <a href="{bot_link}">открыть бота</a>
      </button>
    </div>

    <script>
      document.querySelector(".copy").addEventListener("click", function (e) {
        document.querySelector("input").select();
        document.execCommand("copy");
        this.innerText = "Copied!";
      });
    </script>
  </body>
</html>
"""
redirect_new_page = """
<!DOCTYPE html>
<html>
  <head>
    <title>Center an Image using text align center</title>
    <style>
      .img-container {
        text-align: center;
      }
    </style>
  </head>
  <body>
    <div class="img-container"> <!-- Block parent element -->
      <img src="https://images-na.ssl-images-amazon.com/images/I/516Y1L0Y0HL._AC_SX450_.jpg" alt="OK!!!">
    </div>
  </body>
</html>
"""