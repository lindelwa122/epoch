from datetime import datetime as dt
from fnmatch import fnmatch
from hashlib import sha256
from json import dump, load
from os import listdir, makedirs, path, remove, walk
from pathlib import Path
from uuid import uuid4

class EpochVersionControl:
    def __init__(self):
        self._rootpath = '.'
        self._ignorepath = path.join(self._rootpath, '.epochignore')
        self._epochpath = path.join(self._rootpath, '.epoch')
        self._commitspath = path.join(self._epochpath, 'commits')
        self._commits_file_path = path.join(self._commitspath, 'info.json')
        self._stagepath = path.join(self._epochpath, 'stage.json')
        self._snapshotpath = path.join(self._epochpath, 'snapshot')
        self._headpath = path.join(self._epochpath, 'head')
        self._tailpath = path.join(self._epochpath, 'tail')
        self._historypath = path.join(self._epochpath, 'history')
        self._configpath = path.join(self._epochpath, 'config.json')
        self._config_auth_path_dir = path.join('~', '.epoch_auth')
        self._config_auth_path = path.join(self._config_auth_path_dir, 'secret')
        
        # Load patters to ignore
        ip, np = self._load_ignore_patterns()
        self._ignore_patterns = ip
        self._negation_patterns = np


    def repo_exists(self):
        return path.exists(self._epochpath)


    def _load_ignore_patterns(self):
        ignore_patterns, negation_patterns = [self._epochpath], []

        try:
            with open(self._ignorepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments
                    if not line or line.startswith('#'):
                        continue

                    if line.startswith('!'):
                        # Exclude the negation mark (!)
                        negation_patterns.append(line[1:].strip())

                    else:
                        ignore_patterns.append(line)

        except FileNotFoundError:
            pass

        return ignore_patterns, negation_patterns


    def _is_ignore(self, relative_path):
        is_ignored = False

        for pattern in self._ignore_patterns:
            if fnmatch(relative_path, pattern) \
                or relative_path.startswith(pattern.rstrip('/') + '/'):
                    is_ignored = True

        for pattern in self._negation_patterns:
            if fnmatch(relative_path, pattern) \
                or relative_path.startswith(pattern.rstrip('/') + '/'):
                    is_ignored = False

        return is_ignored


    @staticmethod
    def _hash_file(filepath):
        hasher = sha256()

        # Prevent files with the same content from having the same hash
        hasher.update(filepath.encode())
        with open(filepath, 'rb') as f:
            while chunk := f.read(4096):
                hasher.update(chunk)
            return hasher.hexdigest()


    def _find_matching_files(self, patterns):
        paths = []
        for root, _, files in walk(self._rootpath):
            for file in files:
                pathname = path.join(root, file)
                for pattern in patterns:
                    if not pattern.startswith('./') \
                        and not pattern.startswith('../') \
                        and pattern != '.':
                            pattern = './' + pattern
                    if (fnmatch(pathname, pattern) \
                        or pathname.startswith(pattern.rstrip('/') + '/')) \
                        and not self._is_ignore(pathname):
                            paths.append(pathname)
        return paths


    def _list_dir(self, patterns):
        structure = {}

        paths = self._find_matching_files(patterns)
        for filepath in paths:
            if self._is_ignore(filepath):
                continue

            file_hash = self._hash_file(filepath)
            structure[filepath] = file_hash
        return structure


    def init(self):
        # Initializes an empty repository
        try:
            # Create the directory where versions will be maintained
            makedirs(self._epochpath)
        except FileExistsError:
            print('You cannot reinitialize an already existing repository.')
            exit(1)

        # Create a snapshot directory
        makedirs(self._snapshotpath)
        # Create a commits directory
        makedirs(self._commitspath)

        # Create the staging area
        with open(self._stagepath, 'w') as f:
            f.write('{}')

        # Create an empty head file (points to the current commit)
        head = Path(self._headpath)
        head.touch()

        # Create an empty tail file (points to the first commit)
        tail = Path(self._tailpath)
        tail.touch()

        # Create a commit info file
        with open(self._commits_file_path, 'w') as f:
            f.write('{}')

        # Create a config file
        with open(self._configpath, 'w') as f:
            f.write('{}')

        # Create a history file
        with open(self._historypath, 'w') as f:
            f.write('# Historically committed files\n')

        # Feedback
        print('A new epoch repository has been initialized')


    def _load_existing_index(self):
        if path.exists(self._stagepath):
            with open(self._stagepath, 'r') as f:
                return load(f)
        return {}


    def _save_blob(self, filepath, hash_value):
        blob_path = path.join(self._snapshotpath, hash_value)

        # Avoid saving multiple hash blobs
        if not path.exists(blob_path):
            with open(filepath, 'rb') as src, open(blob_path, 'wb') as dst:
                dst.write(src.read())


    def _load_history(self):
        # Get files that have been committed
        history = []
        with open(self._historypath, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip(): continue
                history.append(line.strip())
        return history


    def _is_modified(self, filepath):
        # Load existing index
        index = self._load_existing_index()
        # Load history
        history = self._load_history()

        hash_value = self._hash_file(filepath)
        if filepath in index and index.get(filepath) != hash_value:
            return True

        if filepath in history and filepath not in index:
            last_commit_hash, _ = self._get_hash_from_last_commit(filepath)
            if hash_value != last_commit_hash: 
                return True

        return False


    def _get_head(self):
        with open(self._headpath, 'r') as f:
            return f.read().strip()


    def _find_removed_files(self):
        history = self._load_history()
        files = self._list_dir(self._rootpath)
        removed = []
        for file in history:
            if file not in files: removed.append(file)
        return removed


    def _find_untracked_files(self, filepaths):
        untracked = []
        history = self._load_history()
        index = self._load_existing_index()

        for filepath in filepaths:
            if filepath not in index \
                and filepath not in history \
                and not self._is_ignore(filepath):
                    untracked.append(filepath)

        return untracked


    def stage(self, *patterns):
        if not path.exists(self._snapshotpath):
            makedirs(self._snapshotpath)
        
        paths = self._find_matching_files(patterns)
        untracked = self._find_untracked_files(paths)
        head = self._get_head()
        # If there is previous commits
        if head:
            # Remove files that have not been modified
            paths = [path for path in paths if self._is_modified(path) or path in untracked]
        
        # Load existing index
        existing_index = self._load_existing_index()

        # Create a new snapshot
        new_snapshot = self._list_dir(paths)
        for filepath, hash_value in existing_index.items():
            if filepath in new_snapshot \
                and hash_value == new_snapshot.get(filepath):
                    del new_snapshot[filepath]

        # Merge snapshots
        existing_index.update(new_snapshot)

        for filepath, hash_value in existing_index.items():
            self._save_blob(filepath, hash_value)

        removed_files = self._find_removed_files()
        for file in removed_files:
            for pattern in patterns:
                if pattern == '.' or file in pattern:
                    if file in existing_index:
                        del existing_index[file]
                    new_snapshot[file] = None
                    existing_index['!'+file] = None

        # Save updated index
        with open(self._stagepath, 'w') as f:
            dump(existing_index, f, indent=4)

        if new_snapshot:
            print('Added these files to the staging area:')
            for file in new_snapshot: print(' ' * 4, file)

        return existing_index


    def status(self):
        modified, staged, untracked = [], [], []

        # Load current index (staging area)
        index = self._load_existing_index()
        # Load history (files that have been committed)
        history = self._load_history()
        for filepath in index:
            if filepath in history:
                staged.append({'file': filepath, 'state': 'modified'})
            elif filepath.startswith('!'):
                staged.append({'file': filepath.lstrip('!'), 'state': 'deleted'})
            else:
                staged.append({'file': filepath, 'state': 'new'})

        for root, _, files in walk(self._rootpath):
            for file in files:
                filepath = path.join(root, file)

                if filepath not in index \
                    and filepath not in history \
                    and not self._is_ignore(filepath):
                        untracked.append(filepath)

                if self._is_modified(filepath):
                    modified.append({'file': filepath, 'state': 'modified'})

        # Find removed files
        removed_files = self._find_removed_files()
        for file in removed_files:
            if '!'+file in index: continue
            modified.append({'file': file, 'state': 'deleted'})

        if staged:
            print(
'''
Changes to be committed:
    (use "epochvc unstage <file>..." to unstage)
''')
            
            for item in staged:
                file, state = item['file'], item['state']
                print(' ' * 4 * 2, f'\033[32m{state}: {file}\033[0m')

        if modified:
            print(
'''
Changes not staged for commit:
    (use "epochvc add <file>..." to update what will be committed)
    (use "epochvc restore <file>..." to discard changes in the working directory)
''')

            for item in modified:
                file, state = item['file'], item['state']
                print(' ' * 4 * 2, f'\033[31m{state}: {file}\033[0m')

        if untracked:
            print(
'''
Untracked files:
    (use "epochvc add <file>..." to include in what will be committed)
''')
            
            for file in untracked:
                print(' ' * 4 * 2, f'\033[31m{file}\033[0m')

        if not (untracked or modified or staged):
            print('No changes detected!')


    @staticmethod
    def _copy_files(src_path, dst_path, hash_values, skip=[]):
        for root, _, files in walk(src_path):
            for file in files:
                filepath = path.join(root, file)
                if filepath in skip: continue

                _dst_path = path.join(dst_path, file)
                with open(filepath, 'rb') as src, open(_dst_path, 'wb') as dst:
                    dst.write(src.read())


    def commit(self, message):
        # Load existing index
        index = self._load_existing_index()
        if not len(index.keys()):
            print('There\'s nothing to commit')
            exit(1)

        # Generate a commit id
        commit_id = str(uuid4())

        # Find out if this is the first commit or not
        head = None
        with open(self._headpath, 'r+') as f:
            head = f.read().strip()
            f.seek(0)
            f.write(commit_id)


        # Create a commit directory
        commit_dirpath = path.join(self._commitspath, commit_id)
        makedirs(commit_dirpath)

        # Create a snapshot directory
        snapshot_dirpath = path.join(commit_dirpath, 'snapshot')
        makedirs(snapshot_dirpath)

        # Load history
        history = self._load_history()

        # If this is the first commit
        if not head:
            # Copy snapshot info
            snapshot_path = path.join(commit_dirpath, 'snapshot.json')
            with open(snapshot_path, 'w') as f:
                dump(index, f, indent=4)

            # Copy snapshots
            self._copy_files(self._snapshotpath, snapshot_dirpath, index)

            # Record first commit
            with open(self._tailpath, 'w') as f:
                f.write(commit_id)

        else:
            # Copy snapshot info
            prev_snapshot_dirpath = path.join(self._commitspath, head, 'snapshot.json')
            with open(prev_snapshot_dirpath, 'r') as f:
                prev_snapshot_info = load(f)

                # Remove removed files
                for file in list(index.keys()):
                    if file.startswith('!'):
                        del prev_snapshot_info[file.lstrip('!')]
                        del index[file]
                        
                        try: history.remove(file.lstrip('!'))
                        except ValueError: pass

                prev_snapshot_info.update(index)
                snapshot_path = path.join(commit_dirpath, 'snapshot.json')
                with open(snapshot_path, 'w') as f:
                    dump(prev_snapshot_info, f, indent=4)

                prev_snapshot_path = path.join(self._commitspath, head, 'snapshot')
                for hash_value in prev_snapshot_info.values():
                    prev_snapshot_p = path.join(prev_snapshot_path, hash_value)
                    dst_path = path.join(snapshot_dirpath, hash_value)
                    if path.exists(prev_snapshot_p):
                        with open(prev_snapshot_p, 'rb') as src, open(dst_path, 'wb') as dst:
                            dst.write(src.read())

                    else:
                        cur_snapshot_p = path.join(self._snapshotpath, hash_value)
                        with open(cur_snapshot_p, 'rb') as src, open(dst_path, 'wb') as dst:
                            dst.write(src.read())

        # Add commit to the commit file
        with open(self._commits_file_path, 'r+') as f:
            commits = load(f)
            f.seek(0)

            if head: commits[head]['next'] = commit_id
            now = dt.now()
            commits[commit_id] = {
                'message': message,
                'datetime': now.strftime('%A, %d %B %Y, %H:%M:%S'),
                'next': None
            }

            dump(commits, f, indent=4)

        # Clean snapshots after saving them into a commit
        for file in listdir(self._snapshotpath):
            pathname = path.join(self._snapshotpath, file)
            remove(pathname)

        # Remove everything from the staging area
        with open(self._stagepath, 'w') as f:
            f.write('{}')

        # Record committed files in history
        for filename in index:
            if filename not in history: 
                history.append(filename)

        with open(self._historypath, 'w') as f:
            for file in history:
                f.write(file + '\n')

        # Feedback
        print(f'Commit created: {commit_id} {message}')
        for file in index: print(' ' * 4, f'{file} snapshot saved')


    def _get_hash_from_last_commit(self, filepath):
        head = None
        with open(self._headpath) as f:
            head = f.read().strip()

        if not head: return None

        history = self._load_history()
        if filepath not in history: return None

        with open(self._commits_file_path, 'r') as f:
            commits_info = load(f)

        while True:
            snapshot_path = path.join(self._commitspath, head, 'snapshot.json')
            with open(snapshot_path, 'r') as f:
                contents = load(f)
                if filepath in contents: return contents.get(filepath), head

                for commit, value in commits_info.items():
                    if value['next'] == head: head = commit

            if not head: return None

        
    def unstage(self, *patterns):
        index, unstaged = self._load_existing_index(), []

        paths = self._find_matching_files(patterns)
        for pathname in paths:
            if pathname in index: 
                hash_value = index.get(pathname)
                snapshot_path = path.join(self._snapshotpath, hash_value)
                remove(snapshot_path)
                del index[pathname]
                unstaged.append(pathname)
            
        for pathname in list(index.keys()):
            variations = ['.']
            variations.append(pathname.lstrip('!'))
            variations.append(pathname.lstrip('!./'))

            for variation in variations:
                if variation in patterns:
                    del index[pathname]
                    unstaged.append(pathname.lstrip('!'))

        with open(self._stagepath, 'w') as f:
            dump(index, f, indent=4)

        if unstaged:
            print('Removed these files from the staging area:')
            for file in unstaged: print(' ' * 4, file)


    def restore(self, *patterns):
        index, restored = self._load_existing_index(), []
        paths = self._find_matching_files(patterns)
        history = self._load_history()
        for filepath in paths:
            hash_value = index.get(filepath, None)

            if not hash_value and filepath in history: 
                hash_value, commit = self._get_hash_from_last_commit(filepath)
                snapshot_path = path.join(self._commitspath, commit, 'snapshot', hash_value)

            elif not hash_value:
                continue

            else:
                snapshot_path = path.join(self._snapshotpath, hash_value)

            with open(snapshot_path, 'rb') as src, open(filepath, 'w') as dst:
                dst.write(src.read().decode())

            restored.append(filepath)

        if restored:
            print('Restored these files:')
            for file in restored: print(' ' * 4, file)


    def log(self):
        with open(self._commits_file_path, 'r') as f:
            commits, entries = load(f), []

            tail = None
            with open(self._tailpath, 'r') as g:
                tail = g.read().strip()

            if not tail:
                print('No commits yet.')
                exit(1)

            while True:
                entries.append(tail)
                tail = commits.get(tail)['next']
                if not tail: break
            
            for i, entry in enumerate(reversed(entries)):
                commit = commits[entry]
                print('commit', 
                      f'\033[33m{entry}\033[0m{" (HEAD)" if not i else ""}', 
                      f'\n{" " * 4}{commit["message"]}', 
                      f'\n{" " * 4}{commit["datetime"]}',
                      end='\n\n'
                )

        
    def revert(self, commit_id):
        # Check if commit is there
        with open(self._commits_file_path, 'r') as f:
            commits = load(f)
            if commit_id not in commits:
                print(f'Commit ID {commit_id} was not found')
                exit(1)

        # SAVE THE CURRENT STAGING AREA
        snapshot = {}
        with open(self._stagepath, 'r') as f:
            staging_area = load(f)

        for hash_value in staging_area.values():
            if not hash_value: continue
            snapshot_path = path.join(self._snapshotpath, hash_value)
            with open(snapshot_path, 'rb') as f:
                snapshot[snapshot_path] = f.read()

        # UPDATE THE STAGING AREA TO MATCH THE OLD COMMIT
        old_commit_stage_path = path.join(self._commitspath, commit_id, 'snapshot.json')
        with open(old_commit_stage_path, 'r') as f, open(self._stagepath, 'w') as g:
            old_snapshot = load(f)
            dump(old_snapshot, g, indent=4)

        # Empty snapshot
        for file in listdir(self._snapshotpath):
            pathname = path.join(self._snapshotpath, file)
            remove(pathname)

        # Copy snapshots
        snapshot_path = path.join(self._commitspath, commit_id, 'snapshot')
        for root, _, files in walk(snapshot_path):
            for file in files:
                src_path = path.join(root, file)
                dst_path = path.join(self._snapshotpath, file)
                with open(src_path, 'rb') as src, open(dst_path, 'wb') as dst:
                    dst.write(src.read())

        for filepath, hash_value in old_snapshot.items():
            src_path = path.join(snapshot_path, hash_value)
            with open(src_path, 'rb') as src, open(filepath, 'w') as dst:
                dst.write(src.read().decode())

        # COMMIT
        self.commit(f'Revert back to {commit_id}')

        # BRING BACK WHAT WAS IN THE STAGING AREA BEFORE THE COMMIT
        with open(self._stagepath, 'w') as f:
            dump(staging_area, f, indent=4)

        for snapshot_path, data in snapshot.items():
            with open(snapshot_path, 'wb') as f:
                f.write(data)

        # Feedback
        print(f'Reverted back to {commit_id}')


    def set_config(self, secret):
        path = Path(self._config_auth_path_dir).expanduser()
        path.mkdir(exist_ok=True, parents=True)

        with open(self._config_auth_path, 'w') as f:
            f.write(secret)

        print('secret saved!')
