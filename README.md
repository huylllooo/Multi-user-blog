Multi User Blog
===============================

A multi user blog application using Google App Engine and Jinja. Users can post blog posts after signing in. Also they are able to leave 'Like' and 'Comment' on others' posts on the blog.

## Getting Started

The site can be accessed here: [`https://upheld-world-157905.appspot.com/`](https://upheld-world-157905.appspot.com/)

Or you can clone the repository on your computer to run it locally

## Running locally

1. Prompt your console to '..\multi_user_blog'
3. Type in the command command 'main.py app.yaml'
4. Open up your browser, go to [`http://localhost:[your_port]`](http://localhost:[your_port]])

## Functionality

### Code Functionality
* App is built using Google App Engine
* Publicly accessible

### Site Usability
* The signup, login/logout, editing/viewing workflow is intuitive to a human user

### Accounts and Security
* User accounts and password are secure and appropriately handled
* Account information is properly retained

### Permissions
* Post Edit or Delete are not visible to non-users. Also, users are redirected to the login page when attempting to create, post comment or like a blog post.
* Logged in users can create, edit, or delete blog posts they themselves have created.


