# Setting up Border Watch OSINT: step-by-step guide

You need about 30 minutes and a computer (a phone is too small for these steps). You only do this once. After that it runs by itself every day.

---

## Part 1. Create your GitHub account (5 minutes)

1. Open **https://github.com/signup**.
2. Type your email, make a password, and choose a **username**. Choose something professional: it becomes part of your website address, `https://USERNAME.github.io/border-watch-osint/`.
3. Solve the puzzle, then type the code GitHub emails to you.
4. If asked, choose the **Free** plan. You never need to pay for this project.

## Part 2. Create your repository (3 minutes)

A "repository" (or "repo") is just a project folder that lives on GitHub.

1. Click the **+** at the top right of GitHub, then **New repository**.
2. **Repository name:** `border-watch-osint`
3. **Description:** `Open-source border and migration news monitor, worldwide with a Caribbean focus`
4. Choose **Public**. (GitHub Pages, the free website, needs Public on a free account. That is why only open-source news goes in.)
5. Tick **Add a README file**.
6. Click **Create repository**.

## Part 3. Put the files in (10 minutes)

**Easiest option: let Claude do it.** Go to **https://claude.ai/connect-github**, connect your GitHub account, and allow access to the `border-watch-osint` repository. Then tell Claude in the thread, and Claude uploads all the files for you. Skip to Part 4.

**Do-it-yourself option:**

1. Download `border-watch-osint.zip` from the Claude thread and unzip it (double-click it).
2. In your repository on GitHub click **Add file → Upload files**.
3. Open the unzipped `border-watch-osint` folder, select **everything inside it**, and drag it onto the GitHub page. Folders upload too.
4. At the bottom, click **Commit changes**. ("Commit" means "save".)
5. **The automation file is hidden** (its folder name starts with a dot), so it usually doesn't upload by dragging. Add it by hand:
   1. Click **Add file → Create new file**.
   2. In the name box type exactly `.github/workflows/daily.yml` (the slashes create the folders).
   3. Open `daily.yml` from the zip in Notepad (Windows) or TextEdit (Mac), copy all of it, and paste it into the big box.
   4. Click **Commit changes**.

## Part 4. Allow the robot to save its work (1 minute)

1. In your repository click **Settings** (top menu).
2. Left menu: **Actions → General**.
3. Scroll to **Workflow permissions**, choose **Read and write permissions**, click **Save**.

## Part 5. Turn on your website (2 minutes)

1. Still in **Settings**, left menu: **Pages**.
2. Under **Build and deployment → Source** choose **Deploy from a branch**.
3. Branch: **main**, folder: **/docs**. Click **Save**.
4. Wait 2 minutes and refresh. GitHub shows your link: `https://USERNAME.github.io/border-watch-osint/`. At first it shows the **demo** (invented) data with a red "Demo data" banner.

## Part 6. Run it for real the first time (5 minutes)

1. Click the **Actions** tab. If GitHub asks, click **I understand my workflows, go ahead and enable them**.
2. Left side: click **daily-border-watch-osint**.
3. Right side: **Run workflow**, change the days to **30**, click the green **Run workflow**.
4. Wait about 5 to 10 minutes. A green tick means it worked; a red cross means something failed (send Claude a screenshot).
5. Open your website link again. It now shows real reports from the last 30 days.

From now on it runs every day at 06:00 Jamaica time by itself.

## Part 7. Share it with your team

Send them the website link. The **Download CSV** link opens in Excel, and **Weekly bulletin** gives a printable one-page summary.

---

### Words you will see

- **Repository (repo):** the project folder on GitHub.
- **Commit:** saving a change, with a short note of what changed.
- **Actions:** GitHub's free computers that run the program on a schedule.
- **Pages:** GitHub's free website hosting, which shows the `docs` folder.
- **Workflow:** the instruction file (`daily.yml`) that tells Actions what to do and when.
