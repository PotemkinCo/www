# Swagger (&GitHub)

Easy way to publish Swagger on GitHub pages (as per [this page](https://medium.com/@crshnburn/embed-swagger-ui-in-github-pages-9c77a86b2fd2)):

- enable GitHub pages (don’t forget to choose a source thread & theme)
- put index.html there:

```bash
<html>
    <head>
        <!-- Load the latest Swagger UI code and style from npm using unpkg.com -->
        <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css"/>
        <title>My New API</title>
    </head>
    <body>
        <div id="swagger-ui"></div> <!-- Div to hold the UI component -->
        <script>
            window.onload = function () {
                // Begin Swagger UI call region
                const ui = SwaggerUIBundle({
                    url: "swagger.json", //Location of Open API spec in the repo
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                })
                window.ui = ui
            }
        </script>
    </body>
</html>
```

- change swagger.json to the actual name of the swagger file
- put this file next to the index.html
- Profit!