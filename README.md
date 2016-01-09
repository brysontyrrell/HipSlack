# HipSlack

Link a HipChat chatroom and a Slack channel together to act as ONE continuous chat.

## About

HipSlack is a lightweight Flask app that allows you to bridge a HipChat chatroom and a Slack channel so that users in both services can chat as if they are in the same room. Currently HipSlack only handles chat messages (users only - Slack bots are ignored) but other features like matching emoji/emoticons, transfering file uploads and properly rendering posted links are planned.

## Running HipSlack

You can easily and quickly stand up a HipSlack instance by using **[ngrok](https://ngrok.com/)** on the system that will run the Flask app.

*If you have your own public domain you can leverage that to point to your HipSlack server and skip the **ngrok** section below.*

### Using ngrok

It is recommended if going this route that you have a **paid ngrok account** so you can have a custom subdomain instead of a randomly generated one (*ngrok generates random subdomains each time it is started under the free tier*):

```shell
$ ./ngrok http 443 -subdomain=your-org-hipslack
```

This will start the secure tunnel from the ngrok service to the local system. All traffic to the ngrok URL will redirect via the tunnel to the local system.

### Create the HipSlack Database

HipSlack uses a small SQLite databse to store information about the rooms it bridges. You will need to create this database manually before running the app. You will need to have installed the Python packages from **requirements.txt** before this.

To create the database `cd` into the HipSlack directory, open the `python` ineractive shell and type:

```python
>>> from main import db
>>> db.create_all()
>>> exit()
```

A `hipslack.db` file will be present in the app's directory.

### Running HipSlack

Once you have installed the Python packages from **requirements.txt** using `pip`, start the Flask app by running:

```shell
$ sudo python ./main.py
```

HipSlack is set to `DEBUG` mode in the repository. While you can run the app in this mode you may change this by setting the `Configuration` class's `DEBUG` value to `False`.

## Install into HipChat

HipSlack is written as a standard HipChat plugin. Install it into a room as a custom integration pointing to the JSON capabilities descriptor as described in HipChat's API documentation:

| _https://your.hipslack.address/**hipchat-capabilities**_

Follow the prompts in HipChat to complete the installation. In addition to registering for the webhook to the room, HipSlack will receive an `OAuthID` and `OAuthSecret` which will be used to generate its API access token.

## Configure Slack's WebHooks

For Slack you will need to configure both an **Incoming** and **Outgoing** webhook for the channel that will be linked to HipChat. Both of these can be configured here: [https://your-team.slack.com/apps/build/custom-integration](https://your-team.slack.com/apps/build/custom-integration)

### Incoming WebHook

From the **Build a Custom Integration** page click on **Incoming WebHooks**, select the channel and click **Add Incoming WebHooks Integration**.

You will be taken to a page to customize some additional details about this webhook. Set whatever values you'd like, but you will need to copy the webhook URL and paste it as the value for the HipSlack `Configuration` class's `SLACK_INCOMING_WEBHOOK_URL`. The URL should look like this:

| *https://hooks.slack.com/services/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*

### Outgoing WebHook

From the **Build a Custom Integration** page click on **Outgoing WebHooks** and click **Add Outgoing WebHooks Integration**.

On the next page select the channel. Do **not** enter any trigger words for this outgoing webhook (leaving this blank for a single channel outoing webhook will tell Slack to send *all* chats). In the **URL(s)** section you will need to enter the URL for that HipSlack listens on for Slack:

| _https://your.hipslack.address/**slack-incoming**_

Copy the **Token** and paste it as the value for the HipSlack `Configuration` class's ```SLACK_OUTGOING_WEBHOOK_TOKEN```. You may customize the remaining options for this webhook.

## Known Issues

#### 1) No Support For Multiple Rooms at This Time

Currently HipSlack is not setup to be configurable for unique webhooks from multiple Slack channels. This will change in a future update where the HipChat user will be able to access a configuration page to save the related Slack webhook URL and token values.

## Watch HipSlack in Action

A short YouTube demo of the integration running on test accounts.

[![IMAGE ALT TEXT](https://img.youtube.com/vi/06yMdIjD03g/0.jpg)](http://www.youtube.com/watch?v=06yMdIjD03g "HipSlack")