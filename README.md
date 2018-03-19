A Magic Eight-ball for Slack and Mattermost

# Install

## Installing the python server

clone this repo and install its dependencies

```sh
$ pip install < requirements.txt
```

## Configuring the Mattermost Webhooks

Configure a new outgoing webhook.

* "Content Type" can be either `application/json` or `application/x-www-form-urlencoded`.
* Leave "Trigger Words" blank
* Configure the callback URL as `https://HOST:PORT/outgoing`.

Configure a slash command.

* Add a title and description to your liking.
* Add a command trigger word (I'd suggest either `8`, `eightball`, or `eightbot`).
* Configure the callback URL as `https://HOST:PORT/slash`.
* Consider adding Autocomplete.

## TLS

eightbot supports TLS, which is good, since the outgoing webhook will send all conversations to the eightbot server. You'll want some sort of encryption for that connection.

You have a few options here. You can have eightbot generate a new key each time the server is restarted, or you can generate your own keys and have eightbot refer to them.

By default, eightbot generates a new certificate each time it's started. The downside is that nothing will recognize this key, so while this will make it easy to start the application, you'll have trouble interacting with it.

If the mattermost server doesn't know of this key, you'll need to enable Insecure Outgoing Connections in System Console -> Security -> Connections.

pass `--certificate /PATH/TO/CERTIFICATE` to use a previously-generated certificate.

pass `--insecure` to run over HTTP. This is not recommended.

# Running

## Running the Server

To run over HTTP, use:

Run `eightbot.py` with python3

```sh
$ python eightbot.py
```

# Usage

the root route returns text

```sh
curl https://HOST:PORT/
Ask again later
```

The `/outgoing` is used for outgoing requests. It will only respond in certain circumstances.

The `/slash` is used for slash commands. It will always respond.
