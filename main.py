from epochvc import EpochVersionControl
from argparse import ArgumentParser

def main():
    parser = ArgumentParser('EpochVC', 'A small version control')
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('init', help='Initialize a new repository')

    add_parser = subparsers.add_parser('add', help='Stage files for commit')
    add_parser.add_argument('patterns', nargs='+', help='Patterns of files to stage')

    subparsers.add_parser('status', help='Show the current status')

    commit_parser = subparsers.add_parser('commit', help='Commit staged changes')
    commit_parser.add_argument('-m', '--message', required=True, help='Commit message')

    unstage_parser = subparsers.add_parser('unstage', help='Unstage files')
    unstage_parser.add_argument('patterns', nargs='+', help='Patterns of files to unstage')

    restore_parser = subparsers.add_parser('restore', help='Restore files to last staged state')
    restore_parser.add_argument('patterns', nargs='+', help='Patterns of files to restore')

    subparsers.add_parser('log', help='Show commit history')

    revert_parser = subparsers.add_parser('revert', help='Revert to a specified commit')
    revert_parser.add_argument('commit', help='Commit id to revert to')

    config_parser = subparsers.add_parser('config', help='Saves the authentication key')
    config_parser.add_argument('auth_key', help='Authentication key')

    args = parser.parse_args()
    vc = EpochVersionControl()
    epoch_repo_exists = vc.repo_exists()

    match args.command:
        case 'init':
            vc.init()

        case 'status':
            if epoch_repo_exists:
                vc.status()
            else:
                print('Use "epoch init" to initialize the repository first.')

        case 'add':
            if epoch_repo_exists:
                patterns = args.patterns
                vc.stage(*patterns)
            else:
                print('Use "epoch init" to initialize the repository first.')

        case 'unstage':
            if epoch_repo_exists:
                patterns = args.patterns
                vc.unstage(*patterns)
            else:
                print('Use "epoch init" to initialize the repository first.')

        case 'commit':
            if epoch_repo_exists:
                message = args.message
                vc.commit(message)
            else:
                print('Use "epoch init" to initialize the repository first.')

        case 'restore':
            if epoch_repo_exists:
                patterns = args.patterns
                vc.restore(*patterns)
            else:
                print('Use "epoch init" to initialize the repository first.')

        case 'revert':
            if epoch_repo_exists:
                commit = args.commit
                vc.revert(commit)
            else:
                print('Use "epoch init" to initialize the repository first.')

        case 'log':
            if epoch_repo_exists:
                vc.log()
            else:
                print('Use "epoch init" to initialize the repository first.')

        case 'config':
            auth_key = args.auth_key
            vc.set_config(auth_key)

if __name__ == '__main__':
    main()