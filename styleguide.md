# コーディングスタイルガイド

> **このドキュメントはプロジェクト全体のコーディング規約を定義します**

---

## 📐 命名規則

### ファイル名
```
✅ Good
user-service.ts
auth-middleware.ts
database-connection.ts

❌ Bad
UserService.ts
Auth_Middleware.ts
databaseconnection.ts
```

**ルール**: `kebab-case`（小文字 + ハイフン区切り）

### クラス・インターフェース
```typescript
✅ Good
class UserService {}
interface UserRepository {}
type ApiResponse = {}

❌ Bad
class userService {}
interface IUserRepository {}  // I プレフィックス不要
type apiResponse = {}
```

**ルール**: `PascalCase`（各単語の先頭大文字）

### 関数・変数
```typescript
✅ Good
const getUserById = () => {}
const isAuthenticated = true
let currentUser = null

❌ Bad
const GetUserById = () => {}
const is_authenticated = true
let CurrentUser = null
```

**ルール**: `camelCase`（最初は小文字、以降の単語は大文字開始）

### 定数
```typescript
✅ Good
const MAX_RETRY_COUNT = 3
const API_BASE_URL = 'https://api.example.com'
const DEFAULT_TIMEOUT_MS = 5000

❌ Bad
const maxRetryCount = 3
const apiBaseUrl = 'https://api.example.com'
```

**ルール**: `UPPER_SNAKE_CASE`（全て大文字 + アンダースコア区切り）

### プライベートメソッド・プロパティ
```typescript
class UserService {
  ✅ Good
  private _cache: Map<string, User>
  private _validateEmail(email: string): boolean {}

  ❌ Bad
  private cache: Map<string, User>
  private validateEmail(email: string): boolean {}
}
```

**ルール**: プレフィックスに`_`（アンダースコア）を付ける

---

## 🔤 TypeScript型定義

### 型注釈の明示
```typescript
✅ Good
function getUser(id: string): Promise<User> {
  return userRepository.findById(id)
}

const users: User[] = await getUsers()

❌ Bad
function getUser(id) {  // 型が不明
  return userRepository.findById(id)
}

const users = await getUsers()  // 型推論に頼りすぎ
```

**ルール**: 関数の引数・戻り値は必ず型を明示

### `any`型の禁止
```typescript
✅ Good
function parseJson(data: string): unknown {
  return JSON.parse(data)
}

const result = parseJson(jsonString)
if (isUser(result)) {
  // 型ガードで安全に使用
  console.log(result.name)
}

❌ Bad
function parseJson(data: string): any {
  return JSON.parse(data)
}
```

**ルール**: `any`は絶対禁止、代わりに`unknown`を使用

### ジェネリクス命名
```typescript
✅ Good
function findById<TEntity>(id: string): Promise<TEntity> {}
class Repository<TModel, TId> {}

❌ Bad
function findById<T>(id: string): Promise<T> {}
class Repository<T, U> {}
```

**ルール**: 単一文字(`T`)より具体的な名前(`TEntity`)を使用

### インターフェース vs Type
```typescript
✅ Good - Interface（拡張可能性がある場合）
interface User {
  id: string
  name: string
}

interface AdminUser extends User {
  permissions: string[]
}

✅ Good - Type（Union/Intersection/複雑な型）
type ApiResponse<T> = {
  data: T
  status: number
} | {
  error: string
  status: number
}

❌ Bad - 一貫性がない
interface User {}  // あるところでは interface
type Product = {}  // あるところでは type
```

**ルール**: 
- オブジェクト定義で拡張が必要 → `interface`
- Union/Intersection/複雑な型 → `type`

---

## 🧩 関数・メソッド設計

### 関数サイズ
```typescript
✅ Good（小さく・単一責務）
function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function validatePassword(password: string): boolean {
  return password.length >= 8
}

function validateUser(user: CreateUserDto): ValidationResult {
  if (!validateEmail(user.email)) {
    return { valid: false, error: 'Invalid email' }
  }
  if (!validatePassword(user.password)) {
    return { valid: false, error: 'Password too short' }
  }
  return { valid: true }
}

❌ Bad（大きすぎる・複数責務）
function validateUser(user: CreateUserDto): ValidationResult {
  // 50行以上のバリデーションロジック...
  // メール検証、パスワード検証、名前検証、住所検証...
}
```

**ルール**: 
- 1関数は30行以内を目安
- 50行を超えたら分割を検討
- 1つの関数は1つの責務のみ

### 引数の数
```typescript
✅ Good（引数をオブジェクトにまとめる）
interface CreateUserOptions {
  email: string
  password: string
  name: string
  role?: string
  isActive?: boolean
}

function createUser(options: CreateUserOptions): Promise<User> {
  // ...
}

await createUser({
  email: 'user@example.com',
  password: 'password123',
  name: 'John Doe',
})

❌ Bad（引数が多すぎる）
function createUser(
  email: string,
  password: string,
  name: string,
  role?: string,
  isActive?: boolean
): Promise<User> {
  // ...
}
```

**ルール**: 引数が3つ以上ならオブジェクトにまとめる

### アーリーリターン
```typescript
✅ Good
function processUser(user: User | null): string {
  if (!user) {
    return 'User not found'
  }
  
  if (!user.isActive) {
    return 'User is inactive'
  }
  
  if (!user.email) {
    return 'Email is required'
  }
  
  // メインロジック
  return `Processing ${user.name}`
}

❌ Bad（ネストが深い）
function processUser(user: User | null): string {
  if (user) {
    if (user.isActive) {
      if (user.email) {
        // メインロジック
        return `Processing ${user.name}`
      } else {
        return 'Email is required'
      }
    } else {
      return 'User is inactive'
    }
  } else {
    return 'User not found'
  }
}
```

**ルール**: ガード節を使ってネストを減らす

---

## 🔄 非同期処理

### async/await優先
```typescript
✅ Good
async function getUsers(): Promise<User[]> {
  const users = await userRepository.findAll()
  const activeUsers = users.filter(u => u.isActive)
  return activeUsers
}

❌ Bad（Promiseチェーン）
function getUsers(): Promise<User[]> {
  return userRepository.findAll()
    .then(users => users.filter(u => u.isActive))
}
```

**ルール**: Promiseチェーンより`async/await`を使用

### 並列処理
```typescript
✅ Good（並列実行）
async function getUserData(userId: string) {
  const [user, posts, comments] = await Promise.all([
    userRepository.findById(userId),
    postRepository.findByUserId(userId),
    commentRepository.findByUserId(userId),
  ])
  
  return { user, posts, comments }
}

❌ Bad（直列実行）
async function getUserData(userId: string) {
  const user = await userRepository.findById(userId)
  const posts = await postRepository.findByUserId(userId)
  const comments = await commentRepository.findByUserId(userId)
  
  return { user, posts, comments }
}
```

**ルール**: 依存関係がない処理は`Promise.all`で並列化

### エラーハンドリング
```typescript
✅ Good
async function fetchUserData(userId: string): Promise<User> {
  try {
    const response = await fetch(`/api/users/${userId}`)
    
    if (!response.ok) {
      throw new ApiError(`Failed to fetch user: ${response.status}`)
    }
    
    const data = await response.json()
    return data
  } catch (error) {
    if (error instanceof ApiError) {
      logger.error('API error', { userId, error: error.message })
      throw error
    }
    
    logger.error('Unexpected error', { userId, error })
    throw new Error('Failed to fetch user data')
  }
}

❌ Bad
async function fetchUserData(userId: string): Promise<User> {
  const response = await fetch(`/api/users/${userId}`)
  const data = await response.json()
  return data  // エラーハンドリングなし
}
```

**ルール**: 
- 外部API呼び出しは必ず try-catch
- エラー時は適切なログ出力
- カスタムエラークラスを使用

---

## 📝 コメント

### Whatではなく Why
```typescript
✅ Good
// ユーザーがプレミアムプランの場合のみキャッシュを使用
// 理由: プレミアムユーザーは頻繁にアクセスするため
if (user.plan === 'premium') {
  return cache.get(userId)
}

❌ Bad
// ユーザーのプランがプレミアムかチェック
if (user.plan === 'premium') {
  return cache.get(userId)
}
```

**ルール**: コードを見ればわかる「何を」ではなく、「なぜ」を書く

### 複雑なロジックには説明
```typescript
✅ Good
// Luhnアルゴリズムでクレジットカード番号を検証
// 参考: https://en.wikipedia.org/wiki/Luhn_algorithm
function validateCreditCard(cardNumber: string): boolean {
  // チェックディジットを除いた数字を右から左に処理
  const digits = cardNumber.replace(/\D/g, '').split('').map(Number)
  
  // 右から2番目の数字から、1つおきに2倍にする
  for (let i = digits.length - 2; i >= 0; i -= 2) {
    digits[i] *= 2
    // 9を超える場合は各桁を足す（または9を引く）
    if (digits[i] > 9) {
      digits[i] -= 9
    }
  }
  
  // すべての数字の合計が10で割り切れればOK
  const sum = digits.reduce((acc, digit) => acc + digit, 0)
  return sum % 10 === 0
}

❌ Bad
function validateCreditCard(cardNumber: string): boolean {
  const digits = cardNumber.replace(/\D/g, '').split('').map(Number)
  for (let i = digits.length - 2; i >= 0; i -= 2) {
    digits[i] *= 2
    if (digits[i] > 9) digits[i] -= 9
  }
  return digits.reduce((a, b) => a + b, 0) % 10 === 0
}
```

### JSDoc（公開API）
```typescript
✅ Good
/**
 * 指定されたユーザーIDのユーザー情報を取得します
 * 
 * @param userId - ユーザーID
 * @returns ユーザー情報
 * @throws {UserNotFoundError} ユーザーが見つからない場合
 * @throws {DatabaseError} データベースエラーが発生した場合
 * 
 * @example
 * ```typescript
 * const user = await getUser('user-123')
 * console.log(user.name)
 * ```
 */
async function getUser(userId: string): Promise<User> {
  // ...
}
```

**ルール**: 公開API・ライブラリの関数にはJSDocを付ける

---

## 🎨 コードフォーマット

### インデント
- **スペース2つ**（タブ禁止）

### 行の長さ
- **最大80文字**（推奨）、100文字（上限）

### セミコロン
- **必須**（TypeScript/JavaScriptともに）

### クォート
- **シングルクォート `'`** 優先
- JSX内は**ダブルクォート `"`**

### 末尾カンマ
```typescript
✅ Good
const user = {
  name: 'John',
  email: 'john@example.com',  // 末尾カンマあり
}

❌ Bad
const user = {
  name: 'John',
  email: 'john@example.com'  // 末尾カンマなし
}
```

---

## 🧪 テストコード

### テストファイル命名
```
src/services/user-service.ts
→ tests/unit/user-service.test.ts

src/controllers/auth-controller.ts
→ tests/integration/auth-controller.test.ts
```

### テストケース構造
```typescript
describe('UserService', () => {
  describe('findById', () => {
    it('should return user when user exists', async () => {
      // Arrange
      const userId = 'user-123'
      const expectedUser = { id: userId, name: 'John' }
      mockRepository.findById.mockResolvedValue(expectedUser)
      
      // Act
      const result = await userService.findById(userId)
      
      // Assert
      expect(result).toEqual(expectedUser)
    })
    
    it('should throw UserNotFoundError when user does not exist', async () => {
      // Arrange
      mockRepository.findById.mockResolvedValue(null)
      
      // Act & Assert
      await expect(userService.findById('invalid-id'))
        .rejects.toThrow(UserNotFoundError)
    })
  })
})
```

**ルール**: Arrange-Act-Assert パターンを使用

---

## 🔒 セキュリティ

### パスワードハッシュ化
```typescript
✅ Good
import bcrypt from 'bcrypt'

const SALT_ROUNDS = 10

async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS)
}

❌ Bad
function hashPassword(password: string): string {
  return btoa(password)  // Base64は暗号化ではない
}
```

### SQLインジェクション対策
```typescript
✅ Good（プリペアドステートメント）
async function getUser(email: string): Promise<User> {
  const query = 'SELECT * FROM users WHERE email = $1'
  const result = await db.query(query, [email])
  return result.rows[0]
}

❌ Bad（文字列連結）
async function getUser(email: string): Promise<User> {
  const query = `SELECT * FROM users WHERE email = '${email}'`
  const result = await db.query(query)
  return result.rows[0]
}
```

### 環境変数
```typescript
✅ Good
const API_KEY = process.env.API_KEY
if (!API_KEY) {
  throw new Error('API_KEY is not defined')
}

❌ Bad
const API_KEY = 'sk-1234567890abcdef'  // ハードコード禁止
```

---

## 📦 Import/Export

### Import順序
```typescript
// 1. 外部ライブラリ
import express from 'express'
import { z } from 'zod'

// 2. 内部モジュール（絶対パス）
import { UserService } from '@/services/user-service'
import { logger } from '@/utils/logger'

// 3. 相対パス
import { validateEmail } from './validators'
import type { CreateUserDto } from './types'
```

### Named Export優先
```typescript
✅ Good
export class UserService {}
export const createUser = () => {}

❌ Bad
export default class UserService {}
```

**ルール**: `default export`より`named export`を優先

---

このスタイルガイドに従うことで、コードの一貫性と保守性が向上します。
Antigravityに`@styleguide.md`で参照させることで、自動的にこのルールに従ったコード生成が可能です。
