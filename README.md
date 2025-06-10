# Epoch

Epoch is a small version control system inspired by Git. It uses similar commands, and the purpose of the project was merely to deeply understand how Git fundamentally works and emulate some of its behaviours. It is built using Python, and it helped me understand the importance of version control, how it works, and a little more about Python.

## How to install

Fork this repo, clone the project into your machine, and run --- to install Epoch in your system. You may want to be inside a virtual environment. Now, run `epochvc --help` to see commands you can run.

## How to contribute

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

1. [Fork](https://github.com/lindelwa122/epoch/fork) this repository.

2. Clone the repository to your own machine by running one of the following commands:

   - HTTPS

   ```
   git clone https://github.com/<your-username>/epoch.git
   ```

   OR

   - SSH

   ```
   git clone git@github.com:<your-username>/epoch.git
   ```

   OR

   - Github CLI:

   ```
   gh repo clone <your-username>/epoch
   ```

3. Create a new branch. The name of the branch must reflect the change you are about to make.

   ```
   git checkout -b <branch-name>
   ```

4. Make your changes or add your new feature. Remember to commit early and commit often. Read our commit rules [here](/COMMIT_RULES.md).

   - Short commit messages:
     ```
     git add <changed-files>
     git commit -m "<commit-message>"
     ```
   - Long commit messages:
     ```
     git add <changed-files>
     git commit
     ```

5. Push your changes to Github by running this command:

   ```
   git push origin <branch-name>
   ```

6. Go over to GitHub and create a pull request. Make sure to include a comment explaining the additions. Please include the issue number being addressed in your comment. For instance, if you were resolving issue 6, add `Issue: #6` at the end of your comment. For more information, please refer to our contributing rules [here](/CONTRIBUTING.md).

## Commands

### Init

Creates an empty repository to store all the snapshots, hashes, and commit information.

### Add

Adds files to the staging area. A hash for each stages file is created using the file's content. This makes it much easier to monitor any changes in the working directory. 

### Status

Shows the status of the project. This includes untracked files, staged files, and modified files.

### Commit

Moves the staged snapshot into its folder in the commit directory. Stores some information about the commit including its hash, message, date, and time. Saves the committed files inside the `history` file, which stores all files that has been committed.

### Unstage

Deletes the snapshots of the files to be unstaged. It also removes the file from `stage.json`.

### Restore

If a file has been modified and an old version of it is in the staging area or committed area, the file could be restored to the latest saved version. 

### Log

Shows the commit history.

### Revert

This is used by specifying a specific commit to revert to. This means a new commit will be created that completely resembles the commit you are trying to revert to. I only found out that this is not how revert actually works with Git after building this feature. I understand how Git does it, but I am still happy with how I did it, and I won't change anything.

To prevent losing any unsaved work, it is wise to stage files before reverting to a certain commit. This will allow you to restore any changes made by the revert.

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

# Contact

Email - [nqabenhlemlaba22@gmail.com](mailto:nqabenhlemlaba22@gmail.com)

LinkedIn - [Nqabenhle Mlaba](https://www.linkedin.com/in/nqabenhle)

Instagram - [Asanda Que](https://www.instagram.com/asanda.que)