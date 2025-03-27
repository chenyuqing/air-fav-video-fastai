# My Favorite Videos

## Description

A web application to store and play your favorite videos from Bilibili and YouTube.

## Features

*   Add videos from Bilibili and YouTube by pasting their links.
*   Fetch video titles automatically.
*   Display video thumbnails (solid color for Bilibili).
*   Play videos in a new tab.
*   Remove videos from the list.
*   Prevent adding duplicate videos.
*   Limit the number of videos to 10.

## Version History

*   **v1.0.0:** Initial release with basic features.
*   **v1.0.1:** Added duplicate video detection and prevention.
*   **v1.0.2:** Fixed duplicate video detection logic.
*   **v1.0.3:** Added URL validation.

## Technologies Used

*   Vue.js
*   JavaScript
*   HTML
*   CSS

## Installation

1.  Clone the repository.
2.  Initialize a Git repository: `git init`
3.  Install dependencies: `npm install` in the `frontend` directory.
4.  Run the development server: `npm run dev` in the `frontend` directory.

## Usage

1.  Open the application in your browser.
2.  Paste a Bilibili or YouTube link into the input field.
3.  Click the "Add Video" button.
4.  Click on a video card to play the video.
5.  Click the "Remove" button to remove a video.

## Deployment

This project can be deployed to Vercel.

1.  Install the Vercel CLI: `npm install -g vercel`
2.  Log in to Vercel: `vercel login`
3.  Deploy the project: `vercel`

## Future Enhancements

*   Implement custom thumbnails for Bilibili videos.
*   Add support for more video platforms.
*   Implement user accounts and video playlists.
