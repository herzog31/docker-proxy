<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <title>Container Port Mappings</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container">
            <h2>Port mappings for {{ baseUrl }}</h2>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Environment</th>
                        <th>Hostname</th>
                        <th>Port</th>
                    </tr>
                </thead>
                <tbody>
                    {% for container in containers %}
                    <tr>
                        <td>{{ container.fullname }}</td>
                        <td>{{ container.name }}</td>
                        <td>{{ container.hostname }}</td>
                        <td><a href="http://{{ container.hostname }}:{{ container.mapPort }}/" target="_blank">{{ container.mapPort }}</a> -> {{ container.privatePort }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </body>
</html>